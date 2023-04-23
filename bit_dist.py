import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.animation import FuncAnimation
import numpy as np
import time

N = 2000
nbits = 8
p = 0  # probability that a bit is zero
T = 10 # sec
grain = 0.005

steps = int(1 / grain)
interval = (T / steps) * 1e3 # ms

plt.style.use("dark_background")
fig, ax = plt.subplots()
ln, = ax.plot([1],[1])

def update(frame):
    p = frame
    nums = np.zeros(N, dtype=int)

    for i in range(nbits):
        nums += (2**i) * (np.random.rand(N) > p)
    
    uq, count = np.unique(nums, return_counts=True)
    dist = np.zeros(2**nbits)
    dist[uq] = count
    dist /= dist.max()
    ln.set_data(range(len(dist)), dist)
    return ln,

def init():
    fig.suptitle("Distribution of random 8-bit numbers where\n$\\Pr(bit_i=0)$"
                 " changes over time (from $0$ to $1$)",
                 fontname="Courier New")
    ax.set_xlim(0, 2**nbits)
    ax.set_ylim(0, 1.1)
    ax.set_xticks([2**x for x in range(4,nbits+1)])
    ax.set_yticks([])
    ax.grid(True, alpha=0.5, linestyle="--")
    return ln,

anim = FuncAnimation(fig, update, frames=np.linspace(0,1,steps), interval=interval,
                     init_func=init, blit=True)
plt.show()

export = False
if export:
    writervideo = matplotlib.animation.PillowWriter(fps=30) 
    anim.save("anim.gif", writer=writervideo)
