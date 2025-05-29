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

class TextColor:
    none = "\033[0m"
    yellow = "\033[93m"
    green = "\033[92m"
    red = "\033[91m"
    bold = "\033[1;97m"

def normalize(input_df):
    b = input_df[args.z].dtype.type(args.normalize)
    estimator = scipy.stats.gmean if args.geomean else np.median
    ref = input_df.groupby([args.x, args.z])[args.y]
    ref = ref.apply(lambda x: estimator(x))
    input_df[args.y] /= input_df[args.x].map(lambda x: ref[(x, b)])

def validate_files():
    global valid_files
    valid_files = []
    valid_formats = [".json", ".csv"]
    for file in args.files:
        if pathlib.Path(file).suffix in valid_formats:
            valid_files.append(file)
        else:
            print(f"ERROR: unsupported file format {file}")

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

def get_time_prefix():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{tcolor.bold}{now}:{tcolor.none} "

def generate_dataframe():
    global df, alive
    dfs = dict()
    for file in local_files:
        file = pathlib.Path(file)
        try:
            if file.suffix == ".json":
                dfs[file.stem] = pd.read_json(file, lines=True)
            elif file.suffix == ".csv":
                dfs[file.stem] = pd.read_csv(file)
        except:
            print("{}{}could not open {}{}".format(
                get_time_prefix(), tcolor.red, file, tcolor.none))

    if len(dfs) == 0:
        print(f"{get_time_prefix()}{tcolor.red}no valid source of data{tcolor.none}")
        alive = False
        sys.exit(1)

    df = pd.concat(dfs)
    df.index.names = ["file", None]
    df = df.reset_index(level=0, drop=(len(dfs) == 1))
    df = df.reset_index(level=0, drop=True)

    if args.filter is None:
        user_filter = dict()
    else:
        user_filter = dict(pair.split("=") for pair in args.filter)
    for k, v in user_filter.items():
        user_filter[k] = df[k].dtype.type(v)

    user_filter = (df[list(user_filter.keys())] == user_filter.values()).all(axis=1)
    df = df[user_filter]

def generate_space():
    global dims, dim_keys, selected_dim, domain, position, z_size, z_dom
    z_size = df[args.z].nunique()
    dims = list(df.columns.difference([args.x, args.y, args.z]))
    if len(dims) > 9:
        print("ERROR: supporting up to 9 free dimensions")
        sys.exit(1)
    dim_keys = "123456789"[:len(dims)]
    selected_dim = dims[0] if len(dims) > 0 else None
    domain = dict()
    position = dict()
    for d in dims:
        domain[d] = df[d].unique()
        position[d] = 0
    z_dom = df[args.z].unique()

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
            generate_dataframe()
            generate_space()
            compute_ylimits()
            space_columns = df.columns.difference([args.y])
            sizes = ["{}={}{}{}".format(
                d, tcolor.bold, df[d].nunique(), tcolor.none) for d in space_columns]
            missing = compute_missing()
            print("{}new space: {}".format(get_time_prefix(), " | ".join(sizes)))
            if len(missing) > 0:
                print("{}{}at least {} missing experiments{}".format(
                    get_time_prefix(),
                    tcolor.yellow, len(missing), tcolor.none))
            update_table()
            update_plot()
        last_hash = current_hash
        time.sleep(1)

def update_table():
    ax_table.clear()
    ax_table.axis("off")
    if len(dims) == 0:
        return
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

    r = sub_df[args.y].max() - sub_df[args.y].min()
    max_digits = int(np.ceil(np.log10(r)))
    y_left, y_right = sub_df[args.y].min(), sub_df[args.y].max()
    y_range = f"[{y_left:.{max_digits}g} - {y_right:.{max_digits}g}]"

    if args.normalize is not None:
        if args.geomean:
            gm_df = sub_df.copy()
            gm_df[args.x] = "geomean"
            cols = gm_df.columns.difference([args.y]).to_list()
            gm_df = gm_df.groupby(cols)[args.y].apply(scipy.stats.gmean).reset_index()
            sub_df = pd.concat([sub_df, gm_df])
        normalize(sub_df)

    if args.speedup is not None:
        c1 = sub_df[args.z] == args.speedup
        c2 = sub_df[args.x] == sub_df[args.x].min()
        baseline = sub_df[(c1 & c2)][args.y].min() 
        sub_df[args.y] = baseline / sub_df[args.y]

    if args.normalize is not None or args.speedup is not None:
        ax_plot.axhline(y=1.0, linestyle="--", linewidth=2, color="orange")

    def custom_error(data):
        d = pd.DataFrame(data)
        return (spread.lower(args.spread_measure)(d),
                spread.upper(args.spread_measure)(d))
    
    preferred_colors = ["#5588dd", "#882255", "#33bb88", "#ddcc77",
                        "#cc6677", "#999933", "#aa44ff", "#448811",
                        "#3fa7d6", "#e94f37", "#6cc551", "#dabef9"]
    
    color_gen = iter(preferred_colors)
    palette = {z: next(color_gen) for z in z_dom}
    palette = "colorblind"

    if args.lines:
        sns.lineplot(data=sub_df, x=args.x, y=args.y, hue=args.z,
                     palette=palette,
                     lw=2, linestyle="-", marker="o",
                     errorbar=None,
                     estimator=np.median)
        spread.draw(ax_plot, [args.spread_measure],
                    sub_df, x=args.x, y=args.y, z=args.z,
                    palette=palette)
    else:
        sns.barplot(
            data=sub_df,
            ax=ax_plot,
            estimator=np.median,
            palette=palette,
            legend=True,
            x=args.x, y=args.y, hue=args.z,
            errorbar=custom_error, alpha=.6)

    if top is not None:
        ax_plot.set_ylim(top=top*padding_factor, bottom=0.0)
    if args.normalize is not None:
        ax_plot.set_ylabel("{} (normalized to {}) {}".format(
            ax_plot.get_ylabel(), args.normalize, y_range))
    elif args.speedup is not None:
        ax_plot.set_ylabel("speedup vs {}\n{}".format(args.speedup, y_range))
        handles, labels = ax_plot.get_legend_handles_labels()
        new_labels = [
            f"{args.speedup} (baseline)" if label == args.speedup else label
            for label in labels
        ]
        # ax_plot.set_xticks(sorted(list(ax_plot.get_xticks()) + [1]))
        ax_plot.legend(handles, new_labels)
    else:
        ax_plot.set_ylabel("{}\n{}".format(args.y, y_range))

    if args.geomean:
        # hacky way to compute the middle point in between two bar groups
        pp = sorted(ax_plot.patches, key=lambda x: x.get_x())
        x = pp[-z_size].get_x() + pp[-z_size-1].get_x() + pp[-z_size-1].get_width()
        plt.axvline(x=x/2, color="grey", linewidth=1, linestyle="-")
    fig.canvas.draw_idle()

def on_key(event):
    global selected_dim
    if selected_dim is None:
        return
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

def compute_missing():
    space_columns = df.columns.difference([args.y])
    expected = set(itertools.product(*[df[col].unique() for col in space_columns]))
    observed = set(map(tuple, df[space_columns].drop_duplicates().values))
    missing = expected - observed
    return pd.DataFrame(list(missing), columns=space_columns)

def validate_options():
    c = 0
    c += 1 if args.normalize is not None else 0
    c += 1 if args.speedup is not None else 0
    if c > 1:
        print("ERROR: specifiy only one among `--normalize`, `--speedup`")
        sys.exit(2)
    if c == 0:
        if args.geomean:
            print("ERROR: `--geomean` can only be used together with `--normalize`")
            sys.exit(2)
    if args.normalize is not None or args.speedup is not None:
        available = df[args.z].unique()
        val = df[args.z].dtype.type(args.normalize or args.speedup)
        if val not in available:
            print("ERROR: `--normalize` and `--speedup`"
                  " must be one of the following values:", available)
            sys.exit(2)
    if args.speedup is not None:
        if not pd.api.types.is_numeric_dtype(df[args.x]):
            print("ERROR: `--speedup` only works when the X-axis has a numeric type.")
            sys.exit(2)

    for col in [args.x, args.y, args.z]:
        if col not in df.columns:
            available = list(df.columns)
            print(f"ERROR: '{col}' is not valid. Available: {available}")
            sys.exit(2)
    if not pd.api.types.is_numeric_dtype(df[args.y]):
        t = df[args.y].dtype 
        print(f"ERROR: Y-axis must have a numeric type. '{args.y}' has type '{t}'")
        sys.exit(1)
    zdom = df[args.z].unique()
    if len(zdom) == 1 and args.geomean:
        print(f"WARNING: `--geomean` is superfluous because "
              f"'{zdom[0]}' is the only value in the '{args.z}' group")
    if args.geomean and args.lines:
        print("ERROR: `--geomean` and `--lines` cannot be used together")
        sys.exit(2)
    if args.x == args.y:
        print(f"ERROR: X-axis and Y-axis must be different dimensions. Given {args.x}")
        sys.exit(2)
    if args.x == args.z or args.y == args.z:
        print(f"ERROR: the `-z` dimension must be different from the dimension used on"
              " the X or Y axis")
        sys.exit(2)
    space_columns = df.columns.difference([args.y])
    for d in space_columns:
        n = df[d].nunique()
        if n > 20 and pd.api.types.is_numeric_dtype(df[d]):
            print(f"WARNING: '{d}' seems to have many ({n}) numeric values."
                  " Are you sure this is not supposed to be the Y-axis?")

    missing = compute_missing()
    if len(missing) > 0:
        print("WARNING: missing experiments:")
        print(missing.to_string(index=False))
        print()

def start_gui():
    global alive
    alive = True
    update_plot()
    update_table()
    threading.Thread(target=file_monitor, daemon=True).start()
    print("{}application running".format(get_time_prefix()))
    plt.show()

def parse_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("files", metavar="FILES", type=str, nargs="+",
        help="JSON Lines or CSV files")
    parser.add_argument("-x", required=True,
        help="X-axis column name")
    parser.add_argument("-y", required=True,
        help="Y-axis column name")
    parser.add_argument("-z", required=True, default=None,
        help="Grouping column name")
    parser.add_argument("-n", "--normalize", default=None,
        help="Normalize w.r.t. a value in -z")
    parser.add_argument("-s", "--speedup", default=None,
        help="Reverse-normalize w.r.t. a value in -z")
    parser.add_argument("-m", "--spread-measure", default="pi95",
        help="Measure of dispersion. Available: " + ", ".join(spread.available))
    parser.add_argument("-r", "--rsync-interval", metavar="S", type=float, default=5,
        help="[seconds] Remote synchronization interval")
    parser.add_argument("-l", "--lines", action="store_true", default=False,
        help="Plot with lines instead of bars")
    parser.add_argument("-g", "--geomean", action="store_true", default=False,
        help="Include a geomean summary")
    parser.add_argument("-f", "--filter", nargs="*",
        help="Filter dimension with explicit values. E.g. -f a=1 b=value")

    args = parser.parse_args()

def compute_ylimits():
    global top
    if len(dims) == 0:
        return
    if args.normalize:
        top = 0
        for config in itertools.product(*domain.values()):
            filt = (df[domain.keys()] == config).all(axis=1)
            df_filtered = df[filt].copy()
            normalize(df_filtered)
            zx = df_filtered.groupby([args.z, args.x])[args.y]
            t = zx.apply(spread.upper(args.spread_measure))
            top = max(top, t.max())
    elif args.speedup:
        c1 = df[args.z] == args.speedup
        c2 = df[args.x] == df[args.x].min()
        not_y = df.columns.difference([args.y]).tolist()
        baseline = df[(c1 & c2)].groupby(not_y)[args.y].min().max()
        top = baseline / df[args.y].min()
    else:
        top = df[args.y].max()

def main():
    global tcolor, top
    tcolor = TextColor()
    top = None
    parse_args()
    validate_files()
    locate_files()
    sync_files()
    generate_dataframe()
    validate_options()
    generate_space()
    compute_ylimits()
    initialize_figure()
    start_gui()

if __name__ == "__main__":
    main()
