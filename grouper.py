import matplotlib.pyplot as plt
import pandas as pd

def plot(**kwargs):
    defaults = dict(reducer="median", geomean=False)
    defaults["reducer"] = "median"
    defaults["xlabel"] = kwargs["xname"]
    defaults["ylabel"] = kwargs["yname"]
    defaults["title"] = ""
    defaults.update(kwargs)
    kwargs.update(defaults)

    df = pd.DataFrame()
    for f in kwargs["files"]:
        d = pd.read_csv(f)
        df = pd.concat([df, d], ignore_index=True)

    gb = df.groupby([kwargs["xname"], kwargs["group"]], as_index=False)[kwargs["yname"]]
    if kwargs["reducer"] in ["min", "max", "mean", "median"]:
        reducer = getattr(gb, kwargs["reducer"])
        rdf = reducer(gb)

    global pdf
    pdf = rdf.pivot(index=kwargs["xname"], columns=kwargs["group"], values=kwargs["yname"])
    pdf.columns = pdf.columns.astype(str)

    gb = df.groupby([kwargs["xname"], kwargs["group"]], as_index=False)[kwargs["yname"]]
    if kwargs["reducer"] in ["min", "max", "mean", "median"]:
        reducer = getattr(gb, kwargs["reducer"])
        rdf = reducer(gb)

    if "baseline" in kwargs:
        g = df[df[kwargs["group"]].astype(str) == kwargs["baseline"]].groupby(kwargs["xname"], as_index=True)[kwargs["yname"]]
        lower_ci = (1.0/pdf).mul(g.min(), axis=0)
        upper_ci = (1.0/pdf).mul(g.max(), axis=0)
        yerr = upper_ci - lower_ci
        yerr.columns = yerr.columns.astype(str)
        pdf = (1.0/pdf).mul(pdf[kwargs["baseline"]], axis=0)
    else:
        yerr = rdf.copy()
        yerr[kwargs["yname"]] = gb.max()[kwargs["yname"]] - gb.min()[kwargs["yname"]]
        yerr = yerr.pivot(index=kwargs["xname"], columns=kwargs["group"], values=kwargs["yname"])
        yerr.columns = yerr.columns.astype(str)

    if "geomean" in kwargs and kwargs["geomean"]:
        pdf.loc["geomean"] = pdf.prod().apply(lambda x: x ** (1/len(pdf)))

    plt.style.use("bmh")
    # plt.figure(figsize=(10, 8), dpi=80)
    pdf.plot(kind="bar", yerr=yerr)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel(kwargs["xlabel"])
    plt.ylabel(kwargs["ylabel"])
    plt.title(kwargs["title"])
    plt.tight_layout()

    if "output" in kwargs:
        plt.savefig(kwargs["output"])
    else:
        plt.show()
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=
        "General grouped-bar performance plot generator",
        argument_default=argparse.SUPPRESS)

    parser.add_argument("files", metavar="INPUT", type=str, nargs="+",
        help="Input CSV files with compatible headers")

    parser.add_argument("-o", "--output", type=str,
        help="Output plot file name. Format is deduced from the extension")

    parser.add_argument("-x", "--xname", type=str, required=True,
        help="Name of the column that should appear on the X axis")

    parser.add_argument("-y", "--yname", type=str, required=True,
        help="Name of the column that should on the Y axis")

    parser.add_argument("-g", "--group", type=str, required=True,
        help="Name of the column that distinguishes bars in the same group")

    parser.add_argument("-r", "--reducer", type=str,
        choices=["min", "max", "mean", "median"],
        help="Group rows by (xname, group) and then apply a reduction (e.g. median)")

    parser.add_argument("--xlabel", type=str,
        help="X axis label")

    parser.add_argument("--ylabel", type=str,
        help="Y axis label")

    parser.add_argument("--title", type=str,
        help="Plot title")

    parser.add_argument("--baseline", type=str,
        help="Which 'group' value represents the baseline")

    parser.add_argument("--geomean", action="store_true",
        help="Add a geomean bar per group")

    # TODO
    # parser.add_argument("--yreverse", type=str,
    #     help="Reverse Y axis")

    args = parser.parse_args()

    plot(**vars(args))
