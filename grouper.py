import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import scipy.stats
import subprocess
import threading
import argparse
import datetime
import pathlib
import hashlib
import spread
import time
import sys

def validate_files():
    valid_files = []
    valid_formats = [".json", ".csv"]
    for file in args.files:
        if pathlib.Path(file).suffix in valid_formats:
            valid_files.append(file)
        else:
            print(f"Unsupported file format {file}")
    return valid_files

def get_local_mirror(rfile):
    return pathlib.Path(rfile.split(":")[1]).name

def locate_files():
    local_files = []
    for file in valid_files:
        if is_remote(file):
            local_files.append(get_local_mirror(file))
        else:
            local_files.append(file)
    return local_files

def generate_input_dataframe():
    global args
    dfs = dict()
    for file in local_files:
        file = pathlib.Path(file)
        if file.suffix == ".json":
            dfs[file.stem] = pd.read_json(file, lines=True)
        elif file.suffix == ".csv":
            dfs[file.stem] = pd.read_csv(file)
    df = pd.concat(dfs)
    df.index.names = ["file", None]
    df = df.reset_index(level=0, drop=(len(dfs) == 1))
    df = df.reset_index(level=0, drop=True)
    return df

def monitor():
    global df
    current_hash = None
    last_hash = None

    while alive:
        try:
            current_hash = ""
            for file in local_files:
                with open(file, "rb") as f:
                    current_hash += hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            current_hash = None
        if current_hash != last_hash:
            df = generate_input_dataframe()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{now}: data updated")
            update_table()
            update_plot()
        last_hash = current_hash
        time.sleep(1)

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

def is_remote(file):
    return "@" in file

def sync_files(interval):
    jobs = []
    for file in valid_files:
        if is_remote(file):
            mirror = get_local_mirror(file)
            proc = subprocess.run(["scp", file, mirror])
            if proc.returncode != 0:
                print(f"scp transfer failed for {file}")
                sys.exit(1)
            jobs.append((file, mirror))

    def rsync(src, dst):
        while alive:
            subprocess.run(
                ["rsync", "-z", "--checksum", src, dst],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(interval)

    for job in jobs:
        threading.Thread(target=rsync, daemon=True, args=job).start()

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

    if args.baseline is not None:
        ref = sub_df.groupby([args.x, args.z])[args.y].median()
        ratio = lambda x: ref[(x, args.baseline)]
        sub_df[args.y] /= sub_df[args.x].map(ratio)
    else:
        top = df[args.y].max()
        ax_plot.set_ylim(top=top, bottom=0.0)

    def custom_error(data):
        d = pd.DataFrame(data)
        return (spread.lower(d, args.spread_measure),
                spread.upper(d, args.spread_measure))

    sns.barplot(
        data=sub_df,
        ax=ax_plot,
        estimator=np.median,
        legend=True,
        x=args.x, y=args.y, hue=args.z,
        errorbar=custom_error, palette="dark", alpha=.6
    )
    fig.canvas.draw_idle()

def on_key(event):
    if event.key in ["left", "right"]:
        update_plot(event.key)
        update_table()
    elif event.key in dim_keys:
        global selected_dim
        selected_dim = dims[int(event.key) - 1]
        update_table()

def on_close(event):
    global alive
    alive = False

parser = argparse.ArgumentParser()
parser.add_argument("files", metavar="FILES", type=str, nargs="+", help="JSON Lines or CSV files")
parser.add_argument("-x", required=True, help="X-axis column name")
parser.add_argument("-y", required=True, help="Y-axis column name")
parser.add_argument("-z", required=False, default=None, help="Grouping column name")
parser.add_argument("-b", "--baseline", default=None, help="Baseline group value in -z to normalize y-axis")
parser.add_argument("-m", "--spread-measure", default="mad", help="Measure of dispersion. Available: " + ", ".join(spread.available))
parser.add_argument("-r", "--rsync-interval", type=float, default=5, help="[seconds] Remote synchronization interval")
args = parser.parse_args()
alive = True
valid_files = validate_files()
local_files = locate_files()
sync_files(args.rsync_interval)

df = generate_input_dataframe()

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
fig.canvas.mpl_connect("key_press_event", on_key)
fig.canvas.mpl_connect("close_event", on_close)
plt.tight_layout()
threading.Thread(target=monitor, daemon=True).start()
plt.show()

