import time
import log

def flat(text):
    def d_wrapper(f, text):
        def f_wrapper(*args, **kwargs):
            log.log(f"[*] Running: {text}")
            t = time.time()
            result = f(*args, **kwargs)
            t = time.time() - t
            log.log(f"[*] {text}: done in {t:.3} s")
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
            log.close("Elapsed: {:.3} s".format(t))
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
            log.__log_plain("done in {:.3} s\n".format(t), end="")
            return result
        return f_wrapper
    return lambda f: d_wrapper(f, text)
