import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import argparse
import pandas
import numpy
import sys

# Dolan E.D., Moŕe J.J.
# 2002
# Benchmarking Optimization Software with Performance Profiles.
# Mathematical Programming 91(2):201–213
# https://link.springer.com/article/10.1007/s101070100263

# ===== COMMAND LINE ARGUMENTS ==========================================================

parser = argparse.ArgumentParser(description=
    "Cumulative Distribution Function plotter. Useful to compare performance on "
    "different methods of the same set of problems.")

parser.add_argument("-t", "--problem-type", type=str, choices=["min", "max"],
    help="Maximization or minimization problem. Default is 'min'", default="min")

parser.add_argument("filename", metavar="CSV_FILE", type=str,
    help="Input CSV file containing a column per method")

parser.add_argument("-r", "--reverse", action="store_true",
    help="Reverse x-axis")

# parser.add_argument("-o", "--output", type=str,
#     help="Specify a file where to dump the plot")

args = parser.parse_args()

if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

# want more than 8 colors? you're screwed
preferred_colors = ["#5588dd", "#882255", "#33bb88", "#ddcc77",
                    "#cc6677", "#999933", "#aa44ff", "#448811"]
preferred_color = iter(preferred_colors)
name_sep = "::"

fig, axs = plt.subplots(1)
plt.style.use("bmh")

if args.problem_type == "min":
    get_best = pandas.DataFrame.min
else:
    get_best = pandas.DataFrame.max

data = pandas.read_csv(args.filename)
best = get_best(data, axis=1)

N = len(data)
y = numpy.linspace(0.0, 1.0, N+1)[1:]

for method in data.columns:
    vals = data[method]
    x = (vals / best).sort_values()

    color = next(preferred_color)
    plt.step(x, y, where="post", label=method, color=color, marker=".")

plt.xlabel("Ratio to best")
fig.suptitle("Performance Profile")
ticks = numpy.linspace(0, 1, 11)
tick_names = [f"{t*100:.0f}%" for t in ticks]
plt.yticks(ticks, tick_names)
plt.legend()
plt.grid(True)
plt.show()

