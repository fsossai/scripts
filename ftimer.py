import time
import flog

unit = "s"

def format(t):
    scale = {"s":1, "ms":1000, "us":1000000, "m":1/60, "h":1/3600}
    t *= scale[unit]
    return f"{t:.3f} {unit}"

class tracker():
    def __init__(self, text):
        self.text = text
        self.ts = []

    def __enter__(self):
        flog.log(self.text + " ... ", end="")
        self.ts.append(time.time())
        return self

    def __exit__(self, *args):
        t = self.ts.pop()
        t = time.time() - t
        flog.plain("took {}\n".format(format(t)), end="")

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            self.__enter__()
            y = f(*args, **kwargs)
            self.__exit__()
            return y
        return wrapper

class flat():
    def __init__(self, text):
        self.ts = []
        self.text = text

    def __enter__(self):
        flog.log(f"[*] Running: {self.text}")
        self.ts.append(time.time())
        return self

    def __exit__(self, *args):
        t = self.ts.pop()
        t = time.time() - t
        tf = format(t)
        flog.log(f"[*] {self.text}: took {tf}")

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            self.__enter__()
            y = f(*args, **kwargs)
            self.__exit__()
            return y
        return wrapper

class section():
    def __init__(self, text):
        self.ts = []
        self.text = text

    def __enter__(self):
        flog.open(self.text)
        self.ts.append(time.time())
        return self

    def __exit__(self, *args):
        t = self.ts.pop()
        t = time.time() - t
        flog.close("Elapsed: {}".format(format(t)))

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            self.__enter__()
            y = f(*args, **kwargs)
            self.__exit__()
            return y
        return wrapper
