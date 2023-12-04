import time
import flog

unit = "s"

def format(t):
    scale = {"s":1, "ms":1000, "us":1000000, "m":1/60, "h":1/3600}
    t *= scale[unit]
    return f"{t:.3f} {unit}"

def flat(text):
    def d_wrapper(f, text):
        def f_wrapper(*args, **kwargs):
            log.log(f"[*] Running: {text}")
            t = time.time()
            result = f(*args, **kwargs)
            t = time.time() - t
            tf = format(t)
            log.log(f"[*] {text}: done in {tf}")
            return result
        return f_wrapper
    return lambda f: d_wrapper(f, text)

def section(text):
    def d_wrapper(f, text):
        def f_wrapper(*args, **kwargs):
            log.open(text)
            t = time.time()
            result = f(*args, **kwargs)
            t = time.time() - t
            log.close("Elapsed: {}".format(format(t)))
            return result
        return f_wrapper
    return lambda f: d_wrapper(f, text)

def task(text):
    def d_wrapper(f, text):
        def f_wrapper(*args, **kwargs):
            log.log(text + " ... ", end="")
            t = time.time()
            result = f(*args, **kwargs)
            t = time.time() - t
            log.__log_plain("done in {}\n".format(format(t)), end="")
            return result
        return f_wrapper
    return lambda f: d_wrapper(f, text)
