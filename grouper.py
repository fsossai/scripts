import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import scipy.stats
import subprocess
import threading
import itertools
import argparse
import datetime
import pathlib
import hashlib
import spread
import time
import sys

def normalize(df):
    if args.normalize is None:
        b = df[args.z].dtype.type(args.baseline)
    else:
        b = df[args.z].dtype.type(args.normalize)
    ref = df.groupby([args.x, args.z])[args.y].median()
    df[args.y] /= df[args.x].map(lambda x: ref[(x, b)])

def validate_files():
    global valid_files
    valid_files = []
    valid_formats = [".json", ".csv"]
    for file in args.files:
        if pathlib.Path(file).suffix in valid_formats:
            valid_files.append(file)
        else:
            print(f"Error: unsupported file format {file}")

def get_local_mirror(rfile):
    return pathlib.Path(rfile.split(":")[1]).name

def locate_files():
    global local_files
    local_files = []
    for file in valid_files:
        if is_remote(file):
            local_files.append(get_local_mirror(file))
        else:
            local_files.append(file)

def initialize_figure():
    global fig, axs, ax_table, ax_plot
    fig, axs = plt.subplots(2, 1, gridspec_kw={"height_ratios": [1, 15]})
    fig.set_size_inches(12, 10)
    ax_table = axs[0]
    ax_plot = axs[1]
    sns.set_theme(style="whitegrid")
    ax_plot.grid(axis="y")
    fig.canvas.mpl_connect("key_press_event", on_key)
    fig.canvas.mpl_connect("close_event", on_close)

def generate_dataframe():
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

def generate_space():
    global df, dims, dim_keys, selected_dim, domain, position
    df = generate_dataframe()
    dims = list(set(df.columns) - {args.x, args.y, args.z})
    if len(dims) > 9:
        print("Error: supporting up to 9 free dimensions")
        sys.exit(1)
    dim_keys = "123456789"[:len(dims)]
    selected_dim = dims[0]
    domain = dict()
    position = dict()
    for d in dims:
        domain[d] = df[d].unique()
        position[d] = 0

def file_monitor():
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
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{now}: data updated")
            generate_space()
            compute_limits()
            update_table()
            update_plot()
        last_hash = current_hash
        time.sleep(1)

def update_table():
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

def sync_files():
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
            time.sleep(args.rsync_interval)

    for job in jobs:
        threading.Thread(target=rsync, daemon=True, args=job).start()

def update_plot(padding_factor=1.05):
    sub_df = df.copy()
    for d in dims:
        k = domain[d][position[d]]
        sub_df = sub_df[sub_df[d] == k]
    ax_plot.clear()

    if args.baseline or args.normalize:
        normalize(sub_df)
        ax_plot.axhline(y=1.0, linestyle="--", linewidth=2, color="orange")

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
    ax_plot.set_ylim(top=top*padding_factor, bottom=0.0)
    if args.baseline is not None:
        ax_plot.set_ylabel("{} (normalized)".format(ax_plot.get_ylabel()))
    elif args.normalize is not None:
        ax_plot.set_ylabel("{} (normalized to {})".format(ax_plot.get_ylabel(),
                                                          args.normalize))

    fig.canvas.draw_idle()

def on_key(event):
    global selected_dim
    if event.key in ["left", "right", "enter", " ", "up", "down"]:
        if event.key in ["right", " ", "enter", "up"]:
            x = 1
        elif event.key in ["left", "down"]:
            x = -1
        cur_pos = position[selected_dim]
        new_pos = (cur_pos + x) % domain[selected_dim].size
        position[selected_dim] = new_pos
        update_plot()
        update_table()
    elif event.key in dim_keys:
        selected_dim = dims[int(event.key) - 1]
        update_table()

def on_close(event):
    global alive
    alive = False

def validate_baseline():
    if args.baseline is not None and args.normalize is not None:
        print("Error: specifiy either `--baseline` or `--normalize`, not both")
        sys.exit(1)
    if args.baseline is None:
        return
    available = df[args.z].unique()
    if df[args.z].dtype.type(args.baseline) not in available:
        print("Error: baseline must be one of the following values:", available)
        sys.exit(1)

def start_gui():
    global alive
    alive = True
    threading.Thread(target=file_monitor, daemon=True).start()
    plt.show()

def parse_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("files", metavar="FILES", type=str, nargs="+", help="JSON Lines or CSV files")
    parser.add_argument("-x", required=True, help="X-axis column name")
    parser.add_argument("-y", required=True, help="Y-axis column name")
    parser.add_argument("-z", required=False, default=None, help="Grouping column name")
    parser.add_argument("-b", "--baseline", default=None, help="Baseline group value in -z to normalize y-axis")
    parser.add_argument("-m", "--spread-measure", default="mad", help="Measure of dispersion. Available: " + ", ".join(spread.available))
    parser.add_argument("-r", "--rsync-interval", metavar="S", type=float, default=5, help="[seconds] Remote synchronization interval")
    parser.add_argument("-n", "--normalize", type=float, default=None, help="Normalize w.r.t. to an explicit value")
    args = parser.parse_args()

def compute_limits():
    global top
    if args.baseline or args.normalize:
        top = 0
        for point in itertools.product(*domain.values()):
            filt = (df[list(domain.keys())] == point).all(axis=1)
            df_filtered = df[filt].copy()
            normalize(df_filtered)
            top = max(top, spread.upper(df_filtered[args.y], args.spread_measure))
    else:
        top = df[args.y].max()

def main():
    parse_args()
    validate_files()
    locate_files()
    sync_files()
    generate_space()
    compute_limits()
    validate_baseline()
    initialize_figure()
    start_gui()

if __name__ == "__main__":
    main()
