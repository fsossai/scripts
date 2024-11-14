import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import scipy.optimize
import argparse
import pandas
import numpy
import sys

# ===== COMMAND LINE ARGUMENTS ==========================================================

parser = argparse.ArgumentParser(
    description="Generating speedup plots from raw time measurements in CSV format.\n"
                "The CSV input files must contain a column named 'threads' and one named 'time' (in ms).\n")

parser.add_argument("filenames", metavar="FILENAMES", type=str, nargs="+",
    help="One or more CSV files containing the columns 'threads' and 'time' (in ms)")

parser.add_argument("-u", "--unit", type=str, choices=["s", "ms"], default="s", 
    help="Time unit. Default is 's' (seconds)")

parser.add_argument("-b", "--baseline", metavar="FILENAME", type=str, default=None, required=True,
    help="The file from which to extract the baseline used for the calculation of the speedup."
         "In case there are runs with different numbers of threads, only thread==1 runs are considered")

parser.add_argument("-c", "--confidence-interval", type=str, choices=["std", "mm", "mad"], default="std",
    help="Policy for the bounds of the intervals. 'std', 'mm', 'mad' stand for"
         "'standard deviation', 'minmax', 'meadian absolute deviation' respectively. Default is 'std'")

parser.add_argument("-s", "--n-sigmas", type=int, choices=[0, 1, 2, 3], default=3,
    help="Confidence intervals expressed in multiples of the standard deviation. "
         "Default is 3. Set to 0 to disable")

parser.add_argument("-X", "--xlim", metavar="NUM", type=float, default=None,
    help="Set a limit for the X axis on the speedup plot")

parser.add_argument("-Y", "--ylim", metavar="NUM", type=float, default=None,
    help="Set a limit for the Y axis on the speedup plot")

parser.add_argument("--ci-style", type=str, choices=["area", "bar"], default="area",
    help="Style to use for plotting confidence intervals. Default is 'area'")

parser.add_argument("--hide-time-plot", default=False, action="store_true",
    help="Hide the absolute time plot")

parser.add_argument("--hide-peaks", action="store_true",
    help="Hide the horizontal and vertical lines related to maximum speedup and minimum execution time")

parser.add_argument("--amdahl", action="store_true",
    help="Attempt to fit Amdahl's law to the speedup plot")

parser.add_argument("--boundaries", action="store_true", default=False,
    help="Draw min-max boundaries around each line")

parser.add_argument("--attitude", type=str, choices=["fair", "pessimistic"], default="pessimistic",
    help="'fair' and 'pessimistic' use 'median' and 'min' for computing a baseline from multiple runs. "
         "Default is 'pessimistic'")

parser.add_argument("-n", "--names", type=str, 
    help="Rename programs in the plot legend. ;-separated list")

parser.add_argument("-t", "--title", type=str, default="",
    help="Figure title")

parser.add_argument("-o", "--output", metavar="FILENAME", type=str,
    help="Specify a file where to dump the plot")

preferred_colors = ["#5588dd", "#882255", "#33bb88", "#ddcc77", "#cc6677", "#999933", "#aa44ff", "#448811"]
preferred_color = iter(preferred_colors)
name_sep = "::"

args = parser.parse_args()

if args.names is not None:
    if len(args.names.split(";")) != len(args.filenames):
        print("ERROR: the number of input files and names do not match")
        sys.exit(1)
    name_it = iter(args.names.split(";"))

fig = plt.figure(constrained_layout=True)
if args.hide_time_plot:
    gs = gridspec.GridSpec(1, 1, figure=fig)
    axs2 = fig.add_subplot(gs[0, 0])
    axs2.set_visible(False)
else:
    gs = gridspec.GridSpec(1, 2, figure=fig)
    axs2 = fig.add_subplot(gs[0, 1])
    axs2.set_visible(True)

axs1 = fig.add_subplot(gs[0, 0])
axs = [axs1, axs2]
plt.style.use("bmh")

def make_line_ci(axes, x, y, low, high, alpha):
    for x_val, y_val, l, h in zip(x, y, low, high):
        axes.vlines(x=x_val, ymin=l, ymax=h, color=color, alpha=alpha, linewidth=4)

# handling baseline
df = pandas.read_csv(args.baseline)
df = df.dropna()
if args.unit == "s":
    df["time"] /= 1000

color = preferred_colors[len(args.filenames)]
baseline_times = df.groupby("threads")["time"].median()

if args.attitude == "fair":
    baseline_time = df.groupby("threads")["time"].median()[1]
elif args.attitude == "pessimistic":
    baseline_time = df.groupby("threads")["time"].min()[1]

baseline_std = df.groupby("threads")["time"].std()
baseline_std = baseline_std.fillna(0.0)
baseline_mins = df.groupby("threads")["time"].min()
baseline_maxs = df.groupby("threads")["time"].max()
f_mad = lambda x : (x - x.median()).abs().median()
baseline_mad = df.groupby("threads")["time"].apply(f_mad)

def upper(sigma_coeff):
    if args.confidence_interval == "std":
        return [baseline_time + sigma_coeff * baseline_std[1]]
    elif args.confidence_interval == "mm":
        return [baseline_maxs[1]]
    elif args.confidence_interval == "mad":
        return [baseline_time + baseline_mad[1]]

def lower(sigma_coeff):
    if args.confidence_interval == "std":
        return [baseline_time - sigma_coeff * baseline_std[1]]
    elif args.confidence_interval == "mm":
        return [baseline_mins[1]]
    elif args.confidence_interval == "mad":
        return [baseline_time - baseline_mad[1]]

# confidence intervals for the baseline (time plot)
if args.n_sigmas >= 1:
    make_line_ci(axs[1], [1], [baseline_time], lower(1), upper(1), alpha=0.30)
if args.n_sigmas >= 2:
    make_line_ci(axs[1], [1], [baseline_time], lower(2), upper(2), alpha=0.20)
if args.n_sigmas >= 3:
    make_line_ci(axs[1], [1], [baseline_time], lower(3), upper(3), alpha=0.10)

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

    nruns = df.groupby("threads").count().max().iloc[0]
    median = df.groupby("threads")["time"].median()
    std = df.groupby("threads")["time"].std()
    std = std.fillna(0.0)
    mins = df.groupby("threads")["time"].min()
    maxs = df.groupby("threads")["time"].max()
    mad = df.groupby("threads")["time"].apply(f_mad)


    # ===== SPEEDUP PLOT ================================================================

    speedup = baseline_time / median
    x = median.index.to_numpy(dtype=int)
    time = median.values

    def upper(sigma_coeff):
        if args.confidence_interval == "std":
            return baseline_time / (median - sigma_coeff*std)
        elif args.confidence_interval == "mm":
            return baseline_time / mins
        elif args.confidence_interval == "mad":
            return baseline_time / (median - mad)

    def lower(sigma_coeff):
        if args.confidence_interval == "std":
            return baseline_time / (median + sigma_coeff*std)
        elif args.confidence_interval == "mm":
            return baseline_time / maxs
        elif args.confidence_interval == "mad":
            return baseline_time / (median + mad)

    label = "{} {} max={:.1f}x @ T={}".format(name, name_sep, max(speedup), speedup.idxmax())

    if min(speedup) < 1.0:
        axs[0].axhline(y=1.0, linestyle="-", linewidth=1, color="#00ff00")

    color = next(preferred_color)
    axs[0].plot(x, speedup, ".-", label=label, color=color)

    # confidence intervals (speedup plot)
    if args.ci_style == "area":
        if args.n_sigmas >= 1:
            axs[0].fill_between(x, lower(1), upper(1), interpolate=True, color=color, alpha=0.15)
        if args.n_sigmas >= 2:
            axs[0].fill_between(x, lower(2), upper(2), interpolate=True, color=color, alpha=0.10)
        if args.n_sigmas >= 3:
            axs[0].fill_between(x, lower(3), upper(3), interpolate=True, color=color, alpha=0.05)
    elif args.ci_style == "bar":
        if args.n_sigmas >= 1:
            make_line_ci(axs[0], x, speedup, lower(1), upper(1), alpha=0.30)
        if args.n_sigmas >= 2:
            make_line_ci(axs[0], x, speedup, lower(2), upper(2), alpha=0.20)
        if args.n_sigmas >= 3:
            make_line_ci(axs[0], x, speedup, lower(3), upper(3), alpha=0.10)

    # Amdalhs's law interpolation
    if args.amdahl:
        amdahls = lambda x, s: 1 / (s + (1 - s) / x)
        par, _ = scipy.optimize.curve_fit(amdahls, x, speedup)
        axs[0].plot(x, amdahls(numpy.array(x), par[0]), "--", color=color, alpha=0.5,
            label="{} {} Amdahl's law, serial={:.1f}%".format(name, name_sep, 100*par[0]))
    
    # Boundaries
    if args.boundaries:
        axs[0].plot(x, baseline_time / maxs, linestyle="--", linewidth=1.0, color=color, alpha=0.5)
        axs[0].plot(x, baseline_time / mins, linestyle="--", linewidth=1.0, color=color, alpha=0.5)

    # ===== TIME PLOT ===================================================================

    label = "{} {} min={:.1f} {} @ T={}".format(name, name_sep, min(time), args.unit, median.index[time.argmin()])
    axs[1].plot(x, time, ".-", label=label, color=color)

    def upper(sigma_coeff):
        if args.confidence_interval == "std":
            return time + sigma_coeff*std
        elif args.confidence_interval == "mm":
            return maxs
        elif args.confidence_interval == "mad":
            return time + mad

    def lower(sigma_coeff):
        if args.confidence_interval == "std":
            return time - sigma_coeff*std
        elif args.confidence_interval == "mm":
            return mins
        elif args.confidence_interval == "mad":
            return time - mad

    # confidence intervals (time plot)
    if args.ci_style == "area":
        if args.n_sigmas >= 1:
            axs[1].fill_between(x, lower(1), upper(1), interpolate=True, color=color, alpha=0.15) 
        if args.n_sigmas >= 2:
            axs[1].fill_between(x, lower(2), upper(2), interpolate=True, color=color, alpha=0.10) 
        if args.n_sigmas >= 3:
            axs[1].fill_between(x, lower(3), upper(3), interpolate=True, color=color, alpha=0.05) 
    elif args.ci_style == "bar":
        if args.n_sigmas >= 1:
            make_line_ci(axs[1], x, time, lower(1), upper(1), alpha=0.30)
        if args.n_sigmas >= 2:
            make_line_ci(axs[1], x ,time, lower(2), upper(2), alpha=0.20)
        if args.n_sigmas >= 3:
            make_line_ci(axs[1], x, time, lower(3), upper(3), alpha=0.10)

    # highlighting highest and lowest peaks
    if not args.hide_peaks:
        axs[0].hlines(y=max(speedup), xmin=0, xmax=speedup.idxmax(), linestyle="--", linewidth=1, color=color)
        axs[1].hlines(y=min(time), xmin=0, xmax=median.index[time.argmin()], linestyle="--", linewidth=1, color=color)

    # printing a brief summary to the terminal
    longest_name = max([len(n) for n in names])
    padding = longest_name + 1
    print("{:{padding}}: max speedup = {:.1f}x ({:.1f} {}) @ T={}".format(name, max(speedup), min(time), args.unit, speedup.idxmax(), padding=padding))

    max_x = max(max_x, df["threads"].max())

color = next(preferred_color)
axs[1].plot(1, baseline_time, marker="*", linestyle="None", markersize=10, color=color, label="Baseline time = {:.1f} {}".format(baseline_time, args.unit))
print("Reference time = {:.1f} {}".format(baseline_time, args.unit))

# print ideal linear speedup
xmax = axs[0].get_xlim()[1]
ymax = axs[0].get_ylim()[1]
axs[0].plot([1, xmax], [1, xmax], linestyle="--", color="lightgray")
axs[0].set_ylim(top=ymax)

x_range = range(2, max_x+1, 2)
axs[0].set_xticks(x_range, x_range, rotation="vertical")
axs[0].set_xlabel("Number of threads (T)")
axs[0].set_ylabel("Speedup")
axs[0].legend()
axs[0].set_ylim(bottom=0.0)
axs[0].set_xlim(left=0)
axs[0].grid(True)
axs[1].set_xticks(x_range, x_range, rotation="vertical")
axs[1].set_xlabel("Number of threads (T)")
axs[1].set_ylabel("Execution time [{}]".format(args.unit))
axs[1].legend()
axs[1].set_ylim(bottom=0.0)
axs[1].set_xlim(left=0)
axs[1].grid(True)
fig.suptitle(args.title)

if args.xlim is not None:
    axs[0].set_xlim(right=args.xlim)

if args.ylim is not None:
    axs[0].set_ylim(top=args.ylim)

if args.output is not None:
    plt.savefig(args.output)
    print("Saved plot to {}".format(args.output))
else:
    plt.show()

