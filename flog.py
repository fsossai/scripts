param = dict()

level=0

def reset_defaults():
    global param
    param["enabled"] = True
    param["vertical_begin"] = "\u250C"
    param["vertical_middle"] = "\u2502"
    param["vertical_end"] = "\u2514"
    param["log_begin"] = "<"
    param["log_end"] = ">" 
    param["open_begin"] = "{"
    param["open_end"] = "}" 
    param["close_begin"] = "[" 
    param["indent_size"] = 1
    param["indent_str"] = "\u2500"
    param["close_end"] = "]"
    param["all_begin"] = "'"
    param["all_end"] = "'\n"
    param["flush"] = True

def __log_plain(*args, **kwargs):
    if not param["enabled"]:
        return
    if "end" not in kwargs:
        kwargs["end"] = param["all_end"]
    if "flush" not in kwargs:
        kwargs["flush"] = param["flush"]

    print(*args, **kwargs)

def log(*args, **kwargs):
    prefix = param["vertical_middle"] + " " * param["indent_size"] * len(param["indent_str"])
    prefix *= level
    prefix += param["all_begin"] + param["log_begin"]
    __log_plain(prefix, end="", flush=False)
    if "end" in kwargs:
        kwargs["end"] += param["log_end"] + param["all_end"]
    else:
        kwargs["end"] = param["log_end"] + param["all_end"]
    __log_plain(*args, **kwargs)

def open(*args, **kwargs):
    global level
    prefix = param["vertical_middle"] + " " * param["indent_size"] * len(param["indent_str"])
    prefix *= level
    prefix += param["vertical_begin"] + param["indent_size"] * param["indent_str"] + param["all_begin"] + param["open_begin"]
    __log_plain(prefix, end="", flush=False)
    kwargs["end"] = param["open_end"] + param["all_end"]
    __log_plain(*args, **kwargs)
    level += 1

def close(*args, **kwargs):
    global level
    level -= 1
    prefix = param["vertical_middle"] + " " * param["indent_size"] * len(param["indent_str"])
    prefix *= level
    prefix += param["vertical_end"] + param["indent_size"] * param["indent_str"] + param["all_begin"] + param["close_begin"]
    __log_plain(prefix, end="", flush=False)
    kwargs["end"] = param["close_end"] + param["all_end"]
    __log_plain(*args, **kwargs)

reset_defaults()
