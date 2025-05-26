import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import argparse
import pathlib
import spread

parser = argparse.ArgumentParser()
parser.add_argument("files", metavar="FILES", type=str, nargs="+", help="JSON Lines or CSV files")
parser.add_argument("-x", required=True, help="X-axis column name")
parser.add_argument("-y", required=True, help="Y-axis column name")
parser.add_argument("-z", required=False, default=None, help="Grouping column name")
parser.add_argument("-b", "--baseline", help="Baseline group value in -z to normalize y-axis")
parser.add_argument("-m", "--spread-measure", default="mad", help="One or more comma-separated measure of dispersion. Available: " + ", ".join(spread.available))
args = parser.parse_args()

# generating input dataframe
dfs = dict()
for file in args.files:
    file = pathlib.Path(file)
    if file.suffix == ".json":
        dfs[file.stem] = pd.read_json(file, lines=True)
    elif file.suffix == ".csv":
        dfs[file.stem] = pd.read_csv(file)
    else:
        print(f"Unsupported file format {file}")
df = pd.concat(dfs)
df.index.names = ["file", None]
df = df.reset_index(level=0)
df = df.reset_index(level=0, drop=True)

def custom_error(data):
    d = pd.DataFrame(data)
    return (spread.lower(d, args.spread_measure),
            spread.upper(d, args.spread_measure))

sns.set_theme(style="whitegrid")
g = sns.catplot(
    data=df, kind="bar",
    x=args.x, y=args.y, hue=args.z,
    errorbar=custom_error, palette="dark", alpha=.6, height=6
)
g.despine(left=True)
g.set_axis_labels(args.x, args.y)

# plt.tight_layout()
plt.show()
