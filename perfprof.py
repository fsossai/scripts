import matplotlib.pyplot as plt
import pathlib
import pandas
import numpy
import sys

# For scientific references see:
#
# Dolan E.D., Moŕe J.J.
# 2002
# Benchmarking Optimization Software with Performance Profiles.
# Mathematical Programming 91(2):201–213
# https://link.springer.com/article/10.1007/s101070100263

def plot(**kwargs):
    defaults = dict()
    defaults["problem_type"] = "min"
    defaults["xlimit"] = 10
    defaults["save"] = False
    defaults["reverse"] = False
    defaults["marker"] = "."
    defaults["marker_size"] = 10
    defaults["title"] = "Performance Profile"
    defaults["xlabel"] = "Ratio to best"
    defaults["ylabel"] = "How many"

    defaults.update(kwargs)
    kwargs.update(defaults)

    fig, axs = plt.subplots(1)

    if kwargs["problem_type"] == "min":
        get_best = pandas.DataFrame.min
    else:
        get_best = pandas.DataFrame.max

    data = pandas.read_csv(kwargs["input"])
    best = get_best(data, axis=1)

    N = len(data)
    y = numpy.linspace(0.0, 1.0, N+1)[1:]

    if "letters" in kwargs:
        if kwargs["letters"] != "":
            if len(kwargs["letters"]) < len(data.columns):
                print("ERROR: not enough letters specified")
                sys.exit(1)

    for i, method in enumerate(data.columns):
        vals = data[method]
        marker = kwargs["marker"]
        if "letters" in kwargs:
            if kwargs["letters"] == "":
                marker = r"${}$".format(chr(ord("A")+i))
            else:
                marker = r"${}$".format(kwargs["letters"][i])
        x = (vals / best).sort_values()
        x = 1 / x if kwargs["reverse"] else x
        plt.step(x, y, where="post", label=method,
                 marker=marker, markersize=kwargs["marker_size"])

    fig.suptitle(kwargs["title"])
    plt.xlabel(kwargs["xlabel"])
    plt.ylabel(kwargs["ylabel"])
    ticks = numpy.linspace(0, 1, 11)
    tick_names = [f"{t*100:.0f}%" for t in ticks]

    plt.yticks(ticks, tick_names)
    if not kwargs["reverse"]:
        plt.xlim(left=1, right=kwargs["xlimit"])
    plt.grid(True, linewidth=0.1)

    if kwargs["problem_type"] == "min":
        if kwargs["reverse"]:
            plt.legend(loc="lower left")
        else:
            plt.legend(loc="lower right")
    else:
        if kwargs["reverse"]:
            plt.legend(loc="upper right")
        else:
            plt.legend(loc="upper left")

    if "output" in kwargs:
        plt.savefig(kwargs["output"])
    elif kwargs["save"]:
        plt.savefig(str(pathlib.Path(kwargs["input"]).with_suffix(".pdf")))
    else:
        plt.show()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=
        "Cumulative Distribution Function plotter. Useful to compare performance on "
        "different methods of the same set of problems.",
        argument_default=argparse.SUPPRESS)

    parser.add_argument("-p", "--problem-type", type=str, choices=["min", "max"],
        help="Maximization or minimization problem. Default is 'min'", default="min")

    parser.add_argument("input", metavar="CSV_FILE", type=str,
        help="Input CSV file containing a column per method")

    parser.add_argument("-x", "--xlimit", type=float, default=10,
        help="Right limit of x-axis. Default is 10")

    parser.add_argument("--xlabel", type=str,
        help="x-axis label")

    parser.add_argument("--ylabel", type=str,
        help="y-axis label")

    parser.add_argument("-s", "--save", action="store_true",
        help="Dump plot to file")

    parser.add_argument("-l", "--letters", type=str,
        help="Use letters as markers. Use \"\" to use ABCDEF...")

    parser.add_argument("-t", "--title", type=str,
        help="Reverse x-axis")

    parser.add_argument("-r", "--reverse", action="store_true",
        help="Reverse x-axis")

    parser.add_argument("-m", "--marker", type=str, default=".",
        help="Set which marker to use. Try '$X$'. Default is '.'")

    parser.add_argument("-z", "--marker-size", type=int, default=10,
        help="Set the size of the marker. Default is 10")

    parser.add_argument("-o", "--output", type=str,
        help="Dump plot to a specified file")

    args = parser.parse_args()
    plt.style.use("dark_background")
    plot(**vars(args))
    

