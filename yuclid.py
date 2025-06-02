from datetime import datetime
import pandas as pd
import subprocess
import itertools
import argparse
import json
import sys
import re
import os

class LogLevel:
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL = 4

def define_text_colors():
    global color
    class TextColors(dict):
        def __init__(self):
            if sys.stdout.isatty():
                self.all = {
                    "none": "\033[0m",
                    "yellow": "\033[93m",
                    "green": "\033[92m",
                    "red": "\033[91m",
                    "bold": "\033[1;97m" 
                }
            else:
                self.all = dict()
        def get_color(self, x):
            return self.all.get(x, "")
        __getattr__ = get_color
    color = TextColors()

def report(level, *pargs, **kwargs):
    timestamp = "{:%Y-%m-%d %H:%M:%S}".format(datetime.now())
    log_prefix = {
        LogLevel.INFO:    f"{color.green}INFO{color.none}",
        LogLevel.WARNING: f"{color.yellow}WARNING{color.none}",
        LogLevel.ERROR:   f"{color.red}ERROR{color.none}",
        LogLevel.FATAL:   f"{color.red}FATAL{color.none}"
    }.get(level, "UNKNOWN")
    kwargs["sep"] = kwargs.get("sep", ": ")
    print(f"{color.bold}yuclid{color.none}", timestamp, log_prefix, *pargs, **kwargs)
    if level == LogLevel.FATAL:
        sys.exit(2)
    if args.abort_on_error and level == LogLevel.ERROR:
        sys.exit(1)

def substitute_point_vars(x, point, point_id):
    pattern = r"\$\{yuclid\.([a-zA-Z0-9_]+)\}"
    y = re.sub(pattern, lambda m: str(point[m.group(1)]["value"]), x)
    pattern = r"\$\{yuclid\.\@\}"
    y = re.sub(pattern, lambda m: f"{args.cache_directory}/{point_id}", y)
    return y

def substitute_global_vars(x):
    pattern = r"\$\{yuclid\.([a-zA-Z0-9_]+)\.values\}"
    y = re.sub(pattern, lambda m: " ".join(space_values[m.group(1)]), x)
    pattern = r"\$\{yuclid\.([a-zA-Z0-9_]+)\.names\}"
    y = re.sub(pattern, lambda m: " ".join(space_names[m.group(1)]), y)
    return y

def read_configuration():
    global data
    with open(args.input, "r") as f:
        data = json.load(f)

def build_environment():
    global env
    env = os.environ.copy()
    env.update({k: str(v) for k, v in data["env"].items()})

def overwrite_configuration():
    global subspace, order, space_size
    space_size = pd.Series([len(v) for k, v in subspace.items()]).prod()
    if args.select is not None:
        new_values = dict(pair.split("=") for pair in args.select)
        for k, values in new_values.items():
            selection = []
            valid = {str(x["name"]): x for x in subspace[k]}
            for current in values.split(","):
                if current in valid.keys():
                    selection.append(valid[current])
            if len(selection) == 0:
                report(LogLevel.FATAL, "empty dimension", k)
            subspace[k] = selection
    if args.order is not None:
        order = args.order.split(",")

def build_space():
    global space, space_names, space_values, space_size
    space = dict()
    for key, values in data["space"].items():
        if key.endswith(":py"):
            name = key.split(":")[-2]
            space[name] = [{"name": x, "value": x} for x in eval(values)]
        else:
            space[key] = []
            for x in values:
                if isinstance(x, str) or isinstance(x, int) or isinstance(x, float):
                    space[key].append({"name": str(x), "value": x})
                elif isinstance(x, dict):
                    if "value" in x:
                        space[key].append({"name": x.get("name", x["value"]),
                                           "value": x["value"]})
    space_values = {key: [x["value"] for x in space[key]] for key in space}
    space_names = {key: [x["name"] for x in space[key]] for key in space}

def define_order():
    global order
    order = list(space.keys())
    for k in data.get("order", []):
        order.append(order.pop(order.index(k)))
    wrong = [k for k in order if k not in space.keys()]
    if len(wrong) > 0:
        report(LogLevel.FATAL, "some dimensions specified in 'order' do not exist",
                ",".join(wrong))

def build_subspace():
    global subspace

    subspace = dict()
    for key, values in space.items():
        subvalues = []
        relevant_presets = {pname: pdims for pname, pdims in selected_presets.items()
                            if key in pdims}
        if len(relevant_presets) == 0:
            subvalues = space[key]
        elif len(relevant_presets) == 1:
            pname, pdims = next(iter(relevant_presets.items()))
            subvalues = [x for x in space[key] if x["name"] in pdims[key]]
        else:
            report(LogLevel.FATAL, f"dimension '{key}' conflicts in presets",
                   ", ".join([pname for pname in relevant_presets]))

        subspace[key] = subvalues

def run_setup():
    setup = []
    if args.dry_run:
        return
    for command in data["setup"]:
        command = substitute_global_vars(command)
        setup.append(command)
    report(LogLevel.INFO, "starting setup")
    errors = False
    for command in setup:
        result = subprocess.run(command, shell=True, env=env)
        if result.returncode != 0:
            errors = True
            report(LogLevel.ERROR, "setup",
                    f"'{command}'",
                    f"failed (code {result.returncode})")
    if errors:
        report(LogLevel.WARNING, "errors have occurred during setup")
    report(LogLevel.INFO, "setup completed")

def point_to_string(point):
    return ".".join([str(x["name"]) for x in point.values()])

def metrics_to_string(mvalues):
    return " ".join([f"{color.bold}{m}{color.none}={v}" for m, v in mvalues.items()])

def get_progress(i):
    return "[{}/{}]".format(i, space_size)

def run_trial(f, i, configuration):
    point = {key: x for key, x in zip(order, configuration)}
    point_id = f"yuclid.{i:08x}.tmp"
    report(LogLevel.INFO, get_progress(i), point_to_string(point), "started")
    command = substitute_global_vars(data["trial"])
    command = substitute_point_vars(data["trial"], point, point_id)
    cmd_result = subprocess.run(command, shell=True, env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    if cmd_result.returncode != 0:
        report(LogLevel.ERROR,
                point_to_string(point),
                f"failed experiment (code {cmd_result.returncode})")
    max_n_metric_values = None
    mvalues = dict()
    for metric, command in data["metrics"].items():
        command = substitute_global_vars(command)
        command = substitute_point_vars(command, point, point_id)
        cmd_result = subprocess.run(command, shell=True, universal_newlines=True,
                                    capture_output=True, env=env)
        if cmd_result.returncode != 0:
            report(LogLevel.ERROR, 
                    point_to_string(point),
                    "failed metric '{}' (code {})".format(
                        metric, cmd_result.returncode))
        cmd_lines = cmd_result.stdout.strip().split("\n")
        mvalues[metric] = [float(line) for line in cmd_lines]
    mvalues_df = pd.DataFrame.from_dict(mvalues, orient="index").transpose()
    if not args.fold:
        # NaN check
        NaNs = mvalues_df.columns[mvalues_df.isnull().any()]
        if len(NaNs) > 0:
            report(LogLevel.WARNING,
                    "the following metrics generated some NaNs",
                    " ".join(list(NaNs)))

    if args.verbose_data:
        result = point
    else:
        result = {k: x["name"] for k, x in point.items()}
    if args.fold:
        result.update(mvalues_df.to_dict(orient="list"))
        f.write(json.dumps(result) + "\n")
    else:
        for record in mvalues_df.to_dict(orient="records"):
            result.update(record)
            f.write(json.dumps(result) + "\n")
    report(LogLevel.INFO,
            "obtained",
            metrics_to_string(mvalues))
    report(LogLevel.INFO,
            get_progress(i+1),
            point_to_string(point),
            "completed")
    f.flush()

def run_trials():
    ordered_space = [subspace[x] for x in order]

    if args.dry_run:
        for i, configuration in enumerate(itertools.product(*ordered_space)):
            point = {key: x for key, x in zip(order, configuration)}
            report(LogLevel.INFO,
                   get_progress(i+1), 
                   "dry run",
                   point_to_string(point))
    else:
        report(LogLevel.INFO, f"writing to '{args.output}'")
        with open(args.output, "a") as f:
            for i, configuration in enumerate(itertools.product(*ordered_space)):
                run_trial(f, i, configuration)

def validate_presets():
    global selected_presets, presets

    presets = data.get("presets", dict())
    for pname, pspace in presets.items():
        for k, values in pspace.items():
            if k not in space:
                report(LogLevel.FATAL, "preset dimension not in space", k)
            if not isinstance(values, list):
                values = [values]
            new_values = []
            wrong = []
            for v in values:
                if isinstance(v, str) and "*" in v:
                    pattern = "^" + re.escape(v).replace("\\*", ".*") + "$"
                    regex = re.compile(pattern)
                    new_values += [n for n in space_names[k] if regex.match(n)]
                elif v not in space_values[k]:
                    print(space_values[k])
                    wrong.append(str(v))
                else:
                    new_values.append(v)
            if len(wrong) > 0:
                report(LogLevel.FATAL, f"unknown values in preset '{pname}'",
                       ", ".join(wrong))
            presets[pname][k] = new_values

    for pname, pspace in presets.items():
        for k, v in pspace.items():
            if len(v) == 0:
                report(LogLevel.ERROR, 
                       f"empty dimension in preset '{pname}'", k)

    if args.presets is None:
        selected_presets = None
    else:
        selected_presets = dict()
        for p in args.presets.split(","):
            if p not in presets:
                report(LogLevel.FATAL, f"preset '{p}' does not exist")
            else:
                selected_presets[p] = presets[p]

def parse_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="yuclid.json",
        help="Specify a configuration file. Default is 'yuclid.json'")
    parser.add_argument("-r", "--order", default=None,
        help="Overwrite space order. E.g. dim1,dim2")
    parser.add_argument("-o", "--output", default=None,
        help="JSON output file path for the generated data")
    parser.add_argument("-p", "--presets", default=None,
        help="Specify a combination of presets to run. E.g. large,machine1")
    parser.add_argument("-s", "--select", nargs="*", default=None,
        help="Select a subset of names/values for each dimension. E.g. dim=val1,val2")
    parser.add_argument("--verbose-data", default=False, action="store_true",
        help="Dump both name and values of dimension")
    parser.add_argument("--fold", default=False, action="store_true",
        help="Fold metric values into an array per experiment")
    parser.add_argument("-A", "--abort-on-error", default=False, action="store_true",
        help="Abort on any error")
    parser.add_argument("--cache-directory", default=".yuclid",
        help="Directory where temporary file will be saved")
    parser.add_argument("--dry-run", default=False, action="store_true",
        help="Show experiment that would run")
    args = parser.parse_args()

def validate_args():
    if args.output is None:
        now = "{:%Y%m%d-%H%M}".format(datetime.now())
        args.output = f"trials.{now}.json"
    elif not args.output.endswith(".json"):
        args.output = f"{args.output}.json"
    if not os.path.isfile(args.input):
        report(LogLevel.FATAL, f"'{args.input}' does not exist")
    os.makedirs(args.cache_directory, exist_ok=True)
    report(LogLevel.INFO, "input configuration", f"'{args.input}'")
    report(LogLevel.INFO, "output data", f"'{args.output}'")

def main():
    parse_args()
    define_text_colors()
    validate_args()
    read_configuration()
    build_environment()
    build_space()
    validate_presets()
    build_subspace()
    overwrite_configuration()
    define_order()
    run_setup()
    run_trials()

if __name__ == "__main__":
    main()
