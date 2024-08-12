import matplotlib.pyplot as plt
import scipy.optimize
import argparse
import pandas
import numpy
import sys

# ===== COMMAND LINE ARGUMENTS ==========================================================

parser = argparse.ArgumentParser(
    description="Generating speedup plots from raw time measurements in CSV format.\n"
                "The CSV input files must contain a column named 'threads' and one named 'time'.")

parser.add_argument("-n", "--names", type=str, help="List of benchmark names (separated by ;)")

parser.add_argument("filenames", metavar="FILE", type=str, nargs="+",
    help="Input CSV file containing the columns 'threads' and 'time'")

parser.add_argument("-u", "--unit", metavar="U", type=str, default="s",
    help="Time unit (e.g. s)")

parser.add_argument("-o", "--output", type=str, help="Specify a file where to dump the plot")

parser.add_argument("-b", "--baseline", metavar="B", type=float,
    help="The baseline reference that will be used to compute the speedup in milliseconds (e.g. best time of the sequential version). "
         "In not specified, the single-thread average running time of FILE is used")

parser.add_argument("-f", "--baseline-file", metavar="BF", type=str, default=None,
    help="The file from which to extract a reference time to use to compute the speedup in milliseconds (e.g. best time of the sequential version). "
         "The value to be used is the minimum running time for threads==1 found in the specified file")

parser.add_argument("-c", "--confidence-interval", type=int, choices=[0, 1, 2, 3], default=2,
    help="Confidence intervals expressed in multiples of the standard deviation. "
         "Default is 3. Set to 0 to disable")

parser.add_argument("--hide-runs", action="store_true",
    help="Hide the number of runs from the figure's legend")

parser.add_argument("--hide-peaks", action="store_true",
    help="Hide the horizontal and vertical lines related to maximum speedup and minimum execution time")

parser.add_argument("-y", "--ci-style", type=str, choices=["area", "line"], default="area",
    help="Style to use for plotting confidence intervals. Default is 'area'")

parser.add_argument("-i", "--interval", type=str, choices=["ci", "mm"], default="ci",
    help="Policy for the bounds of the intervals. 'ci', 'mm' stand for 'confidance interval', 'minmax' respectively. Default is 'ci'")

parser.add_argument("-A", "--amdahl", action="store_true",
    help="Fit Amdahl's law to the speedup plot")

parser.add_argument("-t", "--title", type=str, default="", help="Figure title")

preferred_colors = ["#5588dd", "#882255", "#33bb88", "#ddcc77", "#cc6677", "#999933", "#aa44ff", "#448811"]
preferred_color = iter(preferred_colors)
name_sep = "::"

args = parser.parse_args()

# handling baseline reference
new_time_ref = None
if args.baseline_file is not None:
    df = pandas.read_csv(args.baseline_file)
    df = df.dropna()
    new_time_ref = df.groupby("threads").min()["time"][1]
elif args.baseline is not None:
    new_time_ref = args.baseline

if new_time_ref is not None:
    if args.unit == "s":
        new_time_ref /= 1000

if args.names is not None:
    if len(args.names.split(";")) != len(args.filenames):
        print("ERROR: the number of input files and names do not match")
        sys.exit(1)
    name_it = iter(args.names.split(";"))

fig, axs = plt.subplots(1, 2)
plt.style.use("bmh")

max_x = 1
for filename in args.filenames:
    df = pandas.read_csv(filename)
    df = df.dropna()

    if args.unit == "s":
        df["time"] /= 1000

    nruns = df.groupby("threads").count().max()[0]
    mean = df.groupby("threads")["time"].mean()
    std = df.groupby("threads")["time"].std()
    std = std.fillna(0.0)
    mins = df.groupby("threads")["time"].min()
    maxs = df.groupby("threads")["time"].max()

    if new_time_ref is None:
        time_ref = mins[1]
    else:
        time_ref = new_time_ref

    # ===== SPEEDUP PLOT ================================================================

    speedup = time_ref / mean
    x = mean.index.to_numpy(dtype=int)
    time = mean.values

    def upper(sigma_coeff):
        if args.interval == "ci":
            return time_ref / (mean - sigma_coeff*std)
        elif args.interval == "mm":
            return time_ref / mins

    def lower(sigma_coeff):
        if args.interval == "ci":
            return time_ref / (mean + sigma_coeff*std)
        elif args.interval == "mm":
            return time_ref / maxs

    name=filename.rsplit(".", 1)[0].split("/")[-1] if args.names is None else next(name_it)
    nruns_text = "" if args.hide_runs else " {} runs = {}".format(name_sep, nruns)

    if min(speedup) < 1.0:
        axs[0].axhline(y=1.0, linestyle="-", linewidth=1, color="#00ff00")

    color = next(preferred_color)
    axs[0].plot(x, speedup, ".-", label=name+nruns_text, color=color)

    def make_line_ci(axes, y, low, high, alpha):
        for x_val, y_val, l, h in zip(x, y, low, high):
            axes.vlines(x=x_val, ymin=l, ymax=h, color=color, alpha=alpha, linewidth=4)

    # confidence intervals (speedup plot)
    if args.ci_style == "area":
        if args.confidence_interval >= 1:
            axs[0].fill_between(x, lower(1), upper(1), interpolate=True, color=color, alpha=0.15)
        if args.confidence_interval >= 2:
            axs[0].fill_between(x, lower(2), upper(2), interpolate=True, color=color, alpha=0.10)
        if args.confidence_interval >= 3:
            axs[0].fill_between(x, lower(3), upper(3), interpolate=True, color=color, alpha=0.05)
    elif args.ci_style == "line":
        if args.confidence_interval >= 1:
            make_line_ci(axs[0], speedup, lower(1), upper(1), alpha=0.30)
        if args.confidence_interval >= 2:
            make_line_ci(axs[0], speedup, lower(2), upper(2), alpha=0.20)
        if args.confidence_interval >= 3:
            make_line_ci(axs[0], speedup, lower(3), upper(3), alpha=0.10)

    # Amdalhs's law interpolation
    if args.amdahl:
        amdahls = lambda x, s: 1 / (s + (1 - s) / x)
        par, _ = scipy.optimize.curve_fit(amdahls, x, speedup)
        axs[0].plot(x, amdahls(numpy.array(x), par[0]), "--", color=color, alpha=0.5,
            label="{} {} Amdahl's law, serial={:.1f}%".format(name, name_sep, 100*par[0]))

    # ===== TIME PLOT ===================================================================

    axs[1].plot(x, time, ".-", label=name+nruns_text, color=color)

    def upper(sigma_coeff):
        if args.interval == "ci":
            return time - sigma_coeff*std
        elif args.interval == "mm":
            return mins

    def lower(sigma_coeff):
        if args.interval == "ci":
            return time + sigma_coeff*std
        elif args.interval == "mm":
            return maxs

    # confidence intervals (time plot)
    if args.ci_style == "area":
        if args.confidence_interval >= 1:
            axs[1].fill_between(x, lower(1), upper(1), interpolate=True, color=color, alpha=0.15) 
        if args.confidence_interval >= 2:
            axs[1].fill_between(x, lower(2), upper(2), interpolate=True, color=color, alpha=0.10) 
        if args.confidence_interval >= 3:
            axs[1].fill_between(x, lower(3), upper(3), interpolate=True, color=color, alpha=0.05) 
    elif args.ci_style == "line":
        if args.confidence_interval >= 1:
            make_line_ci(axs[1], time, lower(1), upper(1), alpha=0.30)
        if args.confidence_interval >= 2:
            make_line_ci(axs[1], time, lower(2), upper(2), alpha=0.20)
        if args.confidence_interval >= 3:
            make_line_ci(axs[1], time, lower(3), upper(3), alpha=0.10)

    # highlighting highest and lowest peaks
    if not args.hide_peaks:
        axs[0].hlines(y=max(speedup), xmin=0, xmax=speedup.idxmax(), linestyle="--", linewidth=1, color=color,
            label="{} {} max={:.1f}x @ T={}".format(name, name_sep, max(speedup), speedup.idxmax()))
        axs[0].vlines(x=speedup.idxmax(), ymin=0.0, ymax=max(speedup), linestyle="--", linewidth=1, color=color)
        axs[1].hlines(y=min(time), xmin=0, xmax=mean.index[time.argmin()], linestyle="--", linewidth=1, color=color,
            label="{} {} min={:.1f} {} @ T={}".format(name, name_sep, min(time), args.unit, mean.index[time.argmin()]))
        axs[1].vlines(x=mean.index[time.argmin()], ymin=0, ymax=min(time), linestyle="--", linewidth=1, color=color)

    print("{} ({})\t : max speedup = {:.1f}x @ T={}".format(filename, name, max(speedup), speedup.idxmax()))
    print("{} ({})\t : min time = {:.1f} {} @ T={}".format(filename, name, min(time), args.unit, mean.index[time.argmin()]))
    print()

    max_x = max(max_x, df["threads"].max())

# print baseline reference time
if new_time_ref is not None:
    color = next(preferred_color)
    axs[1].plot(1, new_time_ref, marker="*", linestyle="None", markersize=10, color=color, label="Reference time = {:.1f} {}".format(new_time_ref, args.unit))
    print("Reference time = {:.1f} {}".format(new_time_ref, args.unit))
    print()

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

if args.output is not None:
    plt.get_current_fig_manager().full_screen_toggle()
    plt.savefig(args.output)
else:
    plt.show()

