import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import scipy.stats
import argparse
import pathlib
import spread

def custom_error(data):
    d = pd.DataFrame(data)
    return (spread.lower(d, args.spread_measure),
            spread.upper(d, args.spread_measure))

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
df = df.reset_index(level=0, drop=(len(dfs) == 1))
df = df.reset_index(level=0, drop=True)

# identifying free dimensions
dims = list(set(df.columns) - {args.x, args.y, args.z})
dim_keys = "123456789"[:len(dims)]
selected_dim = dims[0]
domain = dict()
position = dict()
for d in dims:
    domain[d] = df[d].unique()
    position[d] = 0

fig, axs = plt.subplots(2, 1, gridspec_kw={"height_ratios": [1, 10]})
fig.set_size_inches(10, 8)
ax_table = axs[0]
ax_plot = axs[1]

sns.set_theme(style="whitegrid")
ax_plot.grid(axis="y")

def update_table():
    global selected_dim
    ax_table.clear()
    ax_table.axis("off")
    text = [domain[d][position[d]] for d in dims]
    labels = []
    for i, d in enumerate(dims, start=1):
        label = f"{i}: {d}"
        if d == selected_dim:
            label = rf"$\mathbf{{{label}}}$"
        labels.append(label)
    ax_table.table(cellText=[text], colLabels=labels,
                   cellLoc="center", edges="open", loc="center")
    fig.canvas.draw_idle()

def update_plot(direction="none"):
    x = {"left": -1, "right": 1, "none": 0}
    cur_pos = position[selected_dim]
    new_pos = (cur_pos + x[direction]) % domain[selected_dim].size
    position[selected_dim] = new_pos
    sub_df = df.copy()
    for d in dims:
        k = domain[d][position[d]]
        sub_df = sub_df[sub_df[d] == k]
    ax_plot.clear()

    # TODO
    if "baseline" in args:
        estimator = scipy.stats.gmean
        top = df[args.y].max()
    else:
        estimator = np.median
        ax_plot.set_ylim(top=df[args.y].max(), bottom=0.0)
        top = df[args.y].max()

    sns.barplot(
        data=sub_df,
        ax=ax_plot,
        estimator=estimator,
        legend=True,
        x=args.x, y=args.y, hue=args.z,
        errorbar=custom_error, palette="dark", alpha=.6
    )
    ax_plot.set_ylim(top=top, bottom=0.0)
    fig.canvas.draw_idle()

def on_key(event):
    if event.key in ["left", "right"]:
        update_plot(event.key)
        update_table()
    elif event.key in dim_keys:
        global selected_dim
        selected_dim = dims[int(event.key) - 1]
        update_table()

fig.canvas.mpl_connect("key_press_event", on_key)
update_plot()
update_table()

plt.tight_layout()
plt.show()
