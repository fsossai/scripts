param = dict()

level=0

def reset_defaults():
    global param
    param["enabled"] = True
    param["sym_down"] = "\u2502"
    param["sym_right"] = "\u2500 " # or "\u2500"
    param["sym_open"] = "\u250C"
    param["sym_close"] = "\u2514"
    param["end"] = "\n"
    param["flush"] = True

def __log_plain(*args, **kwargs):
    if not param["enabled"]:
        return
    if "end" not in kwargs:
        kwargs["end"] = param["end"]
    if "flush" not in kwargs:
        kwargs["flush"] = param["flush"]

    print(*args, **kwargs)

def log(*args, **kwargs):
    prefix = param["sym_down"] + " " * len(param["sym_right"])
    prefix *= level
    __log_plain(prefix, end="", flush=False)
    __log_plain(*args, **kwargs)

def open(*args, **kwargs):
    global level
    prefix = param["sym_down"] + " " * len(param["sym_right"])
    prefix *= level
    prefix += param["sym_open"] + param["sym_right"]
    level += 1
    __log_plain(prefix, end="", flush=False)
    __log_plain(*args, **kwargs)

def close(*args, **kwargs):
    global level
    level -= 1
    prefix = param["sym_down"] + " " * len(param["sym_right"])
    prefix *= level
    prefix += param["sym_close"] + param["sym_right"]
    __log_plain(prefix, end="", flush=False)
    __log_plain(*args, **kwargs)

reset_defaults()
