import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from scipy.stats import norm
import scipy.optimize
import argparse
import pandas
import numpy
import sys
import re

# ===== COMMAND LINE ARGUMENTS ==========================================================

parser = argparse.ArgumentParser(
    description="Generating speedup plots from raw time measurements in CSV format.\n"
                "The CSV input files must contain a column named 'threads' and one "
                "named 'time' (in ms).\n")

parser.add_argument("filenames", metavar="FILENAMES", type=str, nargs="+",
    help="One or more CSV files containing the columns 'threads' and 'time' (in ms)")

parser.add_argument("-u", "--unit", type=str, choices=["s", "ms"], default="s", 
    help="Time unit. Default is 's' (seconds)")

parser.add_argument("-b", "--baseline", metavar="FILENAME", type=str, default=None,
    help="The file from which to extract the baseline used for the calculation of the speedup."
         "In case there are runs with different numbers of threads, only thread==1 "
         "runs are considered")

parser.add_argument("-m", "--spread-measures", type=str,
    default="std1",
    help="One or more comma-separated measure of dispersion around data. Available: "
         "X standard deviations (stdX), Min-max range (range), "
         "Median absolute deviation (mad), X-percentile (pX). E.g: -m p90,p95")

parser.add_argument("-X", "--xlim", metavar="NUM", type=float, default=None,
    help="Set a limit for the X axis on the speedup plot")

parser.add_argument("-Y", "--ylim", metavar="NUM", type=float, default=None,
    help="Set a limit for the Y axis on the speedup plot")

parser.add_argument("--ci-style", type=str, choices=["area", "bar"], default="area",
    help="Style to use for plotting confidence intervals. Default is 'area'")

parser.add_argument("--hide-plot", type=str, choices=["speedup", "time"], default=None,
    help="Hide a plot")

parser.add_argument("--hide-peaks", action="store_true",
    help="Hide the horizontal and vertical lines related to maximum speed "
          "and minimum execution time")

parser.add_argument("--loglog-time", action="store_true", default=False,
    help="Time plot using log-log axis")

parser.add_argument("--amdahl", action="store_true",
    help="Attempt to fit Amdahl's law to the speedup plot")

parser.add_argument("--boundaries", action="store_true", default=False,
    help="Draw min-max boundaries around each line")

parser.add_argument("--attitude", type=str, choices=["fair", "pessimistic"], default="pessimistic",
    help="'fair' and 'pessimistic' use 'median' and 'min' for computing a baseline from multiple "
         "runs. Default is 'pessimistic'")

parser.add_argument("-n", "--names", type=str, 
    help="Rename programs in the plot legend. ;-separated list")

parser.add_argument("-t", "--title", type=str, default="",
    help="Figure title")

parser.add_argument("-o", "--output", metavar="FILENAME", type=str,
    help="Save figure to a file in different formats. "
         "E.g.: a.pdf, a.svg, a.png, a.jpg")

preferred_colors = ["#5588dd", "#882255", "#33bb88", "#ddcc77",
                    "#cc6677", "#999933", "#aa44ff", "#448811"]
preferred_color = iter(preferred_colors)
name_sep = "::"

args = parser.parse_args()

if args.names is not None:
    if len(args.names.split(";")) != len(args.filenames):
        print("ERROR: the number of input files and names do not match")
        sys.exit(1)
    name_it = iter(args.names.split(";"))

spread_measures = args.spread_measures.split(",")

def compute_mad(x):
    return (x - x.median()).abs().median()

def draw_bar_interval(axes, x, y, lo, up, alpha):
    for x_val, y_val, l, h in zip(x, y, low, high):
        axes.vlines(x=x_val, ymin=lo, ymax=up, color=color, alpha=alpha, linewidth=4)

def lower(y, sm):
    n = re.search(r"\d+", sm)
    if sm.startswith("std"):
        coeff = float(n.group())
        return y.mean() - coeff * y.std()
    elif sm.startswith("p"):
        p = float(n.group()) / 100.0
        coeff = norm.ppf((p + 1.0) / 2.0)
        return y.mean() - coeff * y.std()
    elif sm == "mad":
        return y.mean() - y.apply(compute_mad)
    elif sm == "range":
        return y.min()

def upper(y, sm):
    n = re.search(r"\d+", sm)
    if sm.startswith("std"):
        coeff = float(n.group())
        return y.mean() + coeff * y.std()
    elif sm.startswith("p"):
        p = float(n.group()) / 100.0
        coeff = norm.ppf((p + 1.0) / 2.0)
        return y.mean() + coeff * y.std()
    elif sm == "mad":
        return y.mean() + y.apply(compute_mad)
    elif sm == "range":
        return y.max()

def draw_spread(axes, x, y_lower, y_upper, i):
    if args.ci_style == "area":
        alphas = numpy.linspace(0.15, 0.05, len(spread_measures))
    elif args.ci_style == "bar":
        alphas = numpy.linspace(0.30, 0.10, len(spread_measures))

    if args.ci_style == "area":
        axes.fill_between(x, y_lower, y_upper, interpolate=True, color=color, alpha=alphas[i])
    elif args.ci_style == "bar":
        draw_bar_interval(axes, x, speedup, y_lower, y_upper, alpha=alpha)

fig = plt.figure(constrained_layout=True)

if args.hide_plot is None:
    gs = gridspec.GridSpec(1, 2, figure=fig)
    s_plot = fig.add_subplot(gs[0, 0])
    t_plot = fig.add_subplot(gs[0, 1])
else:
    gs = gridspec.GridSpec(1, 1, figure=fig)
    s_plot = fig.add_subplot(gs[0, 0])
    t_plot = fig.add_subplot(gs[0, 0])

if args.hide_plot == "speedup":
    s_plot.set_visible(False)
elif args.hide_plot == "time":
    t_plot.set_visible(False)

axs = [s_plot, t_plot]
plt.style.use("bmh")

min_thread_num = None
max_thread_num = None

# handling baseline
if args.baseline is not None:
    df = pandas.read_csv(args.baseline)
    df = df.dropna()
    if args.unit == "s":
        df["time"] /= 1000

    color = preferred_colors[len(args.filenames)]
    baseline_times = df.groupby("threads")["time"].median()
    min_thread_num = df["threads"].min()

    if args.attitude == "fair":
        baseline_time = df.groupby("threads")["time"].median()[min_thread_num]
    elif args.attitude == "pessimistic":
        baseline_time = df.groupby("threads")["time"].min()[min_thread_num]

    # confidence intervals for the baseline (time plot)
    alphas = numpy.linspace(0.30, 0.10, len(spread_measures))
    for i, sm in enumerate(spread_measures):
        y_lower = lower(df.groupby("threads")["time"], sm)[:min_thread_num]
        y_upper = upper(df.groupby("threads")["time"], sm)[:min_thread_num]
        draw_bar_interval(t_plot, [min_thread_num], [baseline_time], y_lower, y_upper, alphas[i])

    print("Reference time = {:.1f} {}".format(baseline_time, args.unit))

max_x = 1

names = []
dfs = []

for filename in args.filenames:
    name = filename.rsplit(".", 1)[0].split("/")[-1] if args.names is None else next(name_it)
    names.append(name)
    df = pandas.read_csv(filename)
    dfs.append(df)

for name, df in zip(names, dfs):
    df = df.dropna()

    if args.unit == "s":
        df["time"] /= 1000

    median_times = df.groupby("threads")["time"].median()

    # ===== SPEEDUP PLOT ================================================================

    max_thread_num = max(max_thread_num or 0, df["threads"].max())
    n = df["threads"].min()
    min_thread_num = min(min_thread_num or 2**30, n)
    if min_thread_num != n:
        print("The minumum number of threads in each file should be the same "
              "when no explicit baseline is specified.\n"
              f"Found two experiments with min thread num equal to {min_thread_num} "
              f"and {n} respectively.")
        sys.exit(1)

    if args.baseline is None:
        if args.attitude == "fair":
            baseline_time = df.groupby("threads")["time"].median()[n]
        elif args.attitude == "pessimistic":
            baseline_time = df.groupby("threads")["time"].min()[n]

    speedup = baseline_time / median_times
    x = median_times.index.to_numpy(dtype=int)
    time = median_times.values

    if args.baseline is None:
        # for the case of self speedup (i.e. no explicit baseline) it would be 
        # counterintuitive to not have the speedup plot starting at 1 and the time
        # plot starting from the baseline time
        speedup[min_thread_num] = 1.0
        time[0] = baseline_time

    label = "{} {} max={:.1f}x @ T={}".format(name, name_sep, max(speedup), speedup.idxmax())

    if args.baseline is not None:
        if min(speedup) < 1.0:
            s_plot.axhline(y=1.0, linestyle="-", linewidth=1, color="#00ff00")

    color = next(preferred_color)
    s_plot.plot(x, speedup, ".-", label=label, color=color)

    # confidence intervals (speedup plot)
    for i, sm in enumerate(spread_measures):
        y_lower = lower(df.groupby("threads")["time"], sm)
        y_upper = upper(df.groupby("threads")["time"], sm)
        draw_spread(s_plot, x, baseline_time / y_upper, baseline_time / y_lower, i)

    # Amdalhs's law interpolation
    if args.amdahl:
        amdahls = lambda x, s: 1 / (s + (1 - s) / x)
        par, _ = scipy.optimize.curve_fit(amdahls, x, speedup)
        s_plot.plot(x, amdahls(numpy.array(x), par[0]), "--", color=color, alpha=0.5,
            label="{} {} Amdahl's law, serial={:.1f}%".format(name, name_sep, 100*par[0]))
    
    # Boundaries
    if args.boundaries:
        mins = df.groupby("threads")["time"].min()
        maxs = df.groupby("threads")["time"].max()
        s_plot.plot(x, baseline_time / maxs, linestyle="--", linewidth=1.0, color=color, alpha=0.5)
        s_plot.plot(x, baseline_time / mins, linestyle="--", linewidth=1.0, color=color, alpha=0.5)

    # ===== TIME PLOT ===================================================================

    label = "{} {} min={:.1f} {} @ T={}".format(
            name, name_sep, min(time), args.unit, median_times.index[time.argmin()])
    t_plot.plot(x, time, ".-", label=label, color=color)

    # confidence intervals (time plot)
    for i, sm in enumerate(spread_measures):
        y_lower = lower(df.groupby("threads")["time"], sm)
        y_upper = upper(df.groupby("threads")["time"], sm)
        draw_spread(t_plot, x, y_lower, y_upper, i)

    # highlighting highest and lowest peaks
    if not args.hide_peaks:
        s_plot.hlines(y=max(speedup), xmin=0, xmax=speedup.idxmax(),
                      linestyle="--", linewidth=1, color=color)
        t_plot.hlines(y=min(time), xmin=0, xmax=median_times.index[time.argmin()],
                      linestyle="--", linewidth=1, color=color)

    # printing a brief summary to the terminal
    longest_name = max([len(n) for n in names])
    padding = longest_name + 1
    print("{:{padding}}: max speedup = {:.1f}x ({:.1f} {}) @ T={}"
          .format(name, max(speedup), min(time), args.unit, speedup.idxmax(), padding=padding))

    max_x = max(max_x, df["threads"].max())

# finalizing speedup plot
xmax = s_plot.get_xlim()[1]
ymax = s_plot.get_ylim()[1]
x_range = range(2, max_x+1, 2)
s_plot.plot([1, xmax], [1, xmax], linestyle="--", color="lightgray")
s_plot.set_ylim(top=ymax)
s_plot.set_xticks(x_range, x_range, rotation="vertical")
s_plot.set_xlabel("Number of threads (T)")
s_plot.set_ylabel("Speedup")
s_plot.legend()
s_plot.set_ylim(bottom=0.0)
s_plot.set_xlim(left=min_thread_num-1)
s_plot.set_xlim(right=max_thread_num+1)
s_plot.grid(True)
if args.xlim is not None:
    s_plot.set_xlim(right=args.xlim)
if args.ylim is not None:
    s_plot.set_ylim(top=args.ylim)

# finalizing time plot
color = next(preferred_color)
t_plot.set_xticks(x_range, x_range, rotation="vertical")
t_plot.set_xlabel("Number of threads (T)")
t_plot.set_ylabel("Execution time [{}]".format(args.unit))
t_plot.legend()
t_plot.set_xlim(left=min_thread_num-1)
t_plot.set_xlim(right=max_thread_num+1)
t_plot.grid(True)
if args.loglog_time:
    t_plot.set_xscale("log")
    t_plot.set_yscale("log")
else:
    t_plot.set_ylim(bottom=0.0)
if args.baseline is not None:
    t_plot.plot(1, baseline_time, marker="*", linestyle="None", markersize=10, color=color,
                label="Baseline time = {:.1f} {}".format(baseline_time, args.unit))

# nice title
fig.suptitle(args.title)
if args.hide_plot is None:
    fig.set_size_inches(20, 8)
else:
    fig.set_size_inches(10, 8)

# save to file or show
if args.output is not None:
    plt.savefig(args.output)
    print("Saved plot to {}".format(args.output))
else:
    plt.show()

