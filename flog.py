param = dict()

level=0

class style:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    FUCHSIA = "\033[95m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    NONE = "\033[0m"

def reset_defaults():
    global param
    param["enabled"] = True
    param["vertical.begin"] = "\u250C"
    param["vertical.middle"] = "\u2502"
    param["vertical.end"] = "\u2514"
    param["log.begin"] = ""
    param["log.style"] = style.NONE
    param["log.end"] = ""
    param["open.begin"] = ""
    param["open.style"] = style.NONE
    param["open.end"] = ""
    param["close.begin"] = ""
    param["close.style"] = style.NONE
    param["close.end"] = ""
    param["indent.repeat"] = 1
    param["indent.str"] = "\u2500"
    param["all.begin"] = ""
    param["all.end"] = "\n"
    param["flush"] = True

def plain(*args, **kwargs):
    if not param["enabled"]:
        return
    if "end" not in kwargs:
        kwargs["end"] = param["all.end"]
    if "flush" not in kwargs:
        kwargs["flush"] = param["flush"]

    print(*args, **kwargs)

def log(*args, **kwargs):
    prefix = param["vertical.middle"] + " " * param["indent.repeat"] * len(param["indent.str"])
    prefix *= level
    prefix += param["all.begin"] + param["log.style"] + param["log.begin"]
    plain(prefix, end="", flush=False)
    if "end" not in kwargs:
        kwargs["end"] = param["log.end"] + "\033[0m" + param["all.end"]
    plain(*args, **kwargs)

def open(*args, **kwargs):
    global level
    prefix = param["vertical.middle"] + " " * param["indent.repeat"] * len(param["indent.str"])
    prefix *= level
    prefix += param["vertical.begin"] + param["indent.repeat"] * param["indent.str"] \
            + param["all.begin"] + param["open.style"] + param["open.begin"]
    plain(prefix, end="", flush=False)
    kwargs["end"] = param["open.end"] + style.NONE + param["all.end"]
    plain(*args, **kwargs)
    level += 1

def close(*args, **kwargs):
    global level
    level -= 1
    prefix = param["vertical.middle"] + " " * param["indent.repeat"] * len(param["indent.str"])
    prefix *= level
    prefix += param["vertical.end"] + param["indent.repeat"] * param["indent.str"]\
            + param["all.begin"] + param["close.style"] + param["close.begin"]
    plain(prefix, end="", flush=False)
    kwargs["end"] = param["close.end"] + style.NONE + param["all.end"]
    plain(*args, **kwargs)

reset_defaults()
