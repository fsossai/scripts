import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas
import numpy
import sys
from scipy.stats import norm
from sklearn.mixture import GaussianMixture
from scipy.stats import zscore
from scipy.stats import lognorm
from scipy.stats import exponweib
import scipy.stats
import seaborn as sns

N = len(sys.argv[1:])
f_mad = lambda x: (x - x.median()).abs().median()

ncores = N
nrows = 2
ncols = ncores // 2
fig = plt.figure(constrained_layout=True)
fig.set_size_inches(22, 10)
gs = gridspec.GridSpec(nrows, ncols, figure=fig)
axes = []

left_lim = None
right_lim = None


for col in range(ncols):
    for row in range(nrows):
        axes.append(fig.add_subplot(gs[row, col]))
        

all_times = []
times_sock = [numpy.array([], dtype=numpy.float64), numpy.array([], dtype=numpy.float64)]
for i, arg in enumerate(sys.argv[1:]):
    ax = axes[i % ncores]
    df = pandas.read_csv(arg)
    times = df["time"]
    times_sock[i%2] = numpy.concatenate((times_sock[i%2], times.values))

    def sigma_interval(x, n):
        p = norm.cdf(n)
        return zscore(x).quantile(1-p), zscore(x).quantile(p)
        
    print(arg)
    padding = 15
    print("\t{:{padding}}{:.3f}".format("median", times.median(), padding=padding))
    print("\t{:{padding}}{:.3f}".format("min", times.min(), padding=padding))
    print("\t{:{padding}}{:.3f}".format("mean", times.mean(), padding=padding))
    print("\t{:{padding}}{:.3f}".format("std", times.std(), padding=padding))
    print("\t{:{padding}}{:.3f}".format("MAD", f_mad(times), padding=padding))
    print("\t{:{padding}}[{:.2f}; {:.2f}]".format("Q-Q [-1;1]", *sigma_interval(times, 1), padding=padding))
    print("\t{:{padding}}[{:.2f}; {:.2f}]".format("Q-Q [-2;2]", *sigma_interval(times, 2), padding=padding))
    print("\t{:{padding}}[{:.2f}; {:.2f}]".format("Q-Q [-3;3]", *sigma_interval(times, 3), padding=padding))
    print()
 
    # l = times.quantile(0.00)
    # r = times.quantile(1.00)
    # l = times.median() - 7 * f_mad(times)
    # r = times.median() + 20 * f_mad(times)
    l = times.mean() - 1 * times.std()
    r = times.mean() + 8 * times.std()
    left_lim = left_lim or l
    right_lim = right_lim or l
    left_lim = min(left_lim, l)
    right_lim = max(right_lim, r)

    if row == 0:
        ax.tick_params(bottom=False, labelbottom=False)
    # sns.kdeplot(times, fill=True, ax=ax, label=f"core {i}, socket {i%2}")
    times_trimmed = times
    times_trimmed = times_trimmed[times_trimmed >= l]
    times_trimmed = times_trimmed[times_trimmed <= r]
    if N <= 16:
        ax.text(
            0.95, 0.95, 
            #i,
            "core {}\nmedian = {:.0f}\nstd = {:.2f}\nMAD = {:.2f}".format(
                i, times.median(), times.std(), f_mad(times)),
            fontsize=10,
            va="top", ha="right", 
            transform=ax.transAxes 
        )

    ax.tick_params(left=False, labelleft=False)

    sns.kdeplot(times_trimmed, fill=True, ax=ax, clip=(l, r), bw_adjust=0.4,
                color="mediumpurple", edgecolor="none")

    ymin, ymax = ax.get_ylim()
    ymax *= 0.75
    # ax.vlines(x=times.quantile(0.9), ymin=ymin, ymax=ymax, color="purple", linewidth=2)
    # ax.vlines(x=times.quantile(0.95), ymin=ymin, ymax=ymax, color="purple", linewidth=2)
    # ax.vlines(x=times.quantile(0.99), ymin=ymin, ymax=ymax, color="purple", linewidth=2)
    # ax.vlines(x=times.quantile(norm.cdf(1)), ymin=ymin, ymax=ymax, color="purple", linewidth=2)
    # ax.vlines(x=times.quantile(norm.cdf(2)), ymin=ymin, ymax=ymax, color="purple", linewidth=2)
    # ax.vlines(x=times.quantile(norm.cdf(3)), ymin=ymin, ymax=ymax, color="purple", linewidth=2)

    # ax.vlines(x=times.mean()+1*times.std(), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")
    ax.vlines(x=times.mean()+2*times.std(), ymin=ymin, ymax=ymax, color="red", linewidth=1.5, linestyle="--")
    # ax.vlines(x=times.mean()+3*times.std(), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")

    # ax.vlines(x=times_trimmed.mean()+1*times_trimmed.std(), ymin=ymin, ymax=ymax, color="grey", linewidth=1, linestyle="--")
    # ax.vlines(x=times_trimmed.mean()+2*times_trimmed.std(), ymin=ymin, ymax=ymax, color="grey", linewidth=1, linestyle="--")
    # ax.vlines(x=times_trimmed.mean()+3*times_trimmed.std(), ymin=ymin, ymax=ymax, color="grey", linewidth=1, linestyle="--")

    # ax.vlines(x=times.median()+1*1.5*f_mad(times), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")
    # ax.vlines(x=times.median()+2*1.5*f_mad(times), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")
    # ax.vlines(x=times.median()+3*1.5*f_mad(times), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")

    # ax.vlines(x=times_trimmed.quantile(norm.cdf(1)), ymin=ymin, ymax=ymax, color="grey", linewidth=2)
    ax.vlines(x=times_trimmed.quantile(norm.cdf(2)), ymin=ymin, ymax=ymax, color="purple", linewidth=2.5)
    # ax.vlines(x=times_trimmed.quantile(norm.cdf(3)), ymin=ymin, ymax=ymax, color="grey", linewidth=2)
    # ax.vlines(x=times.mean()+2*times.std(), ymin=ymin, ymax=ymax, color="red", linewidth=2, linestyle="--")
    # ax.vlines(x=times_trimmed.mean()+2*times_trimmed.std(), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")
    # ax.vlines(x=times.mean()+2*times.std(), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")
    # ax.vlines(x=times.mean()+3*times.std(), ymin=ymin, ymax=ymax, color="orange", linewidth=2, linestyle="--")


    x = numpy.linspace(min(times_trimmed), max(times_trimmed), 500)

    gmm = GaussianMixture(n_components=2).fit(times_trimmed.to_numpy().reshape(-1, 1))
    pdf = numpy.exp(gmm.score_samples(x.reshape(-1, 1)))
    ax.plot(x, pdf, color="purple", linewidth=1.5)

    s, loc, scale = scipy.stats.lognorm.fit(times_trimmed)
    pdf = scipy.stats.lognorm.pdf(x, s, loc, scale)
    ax.plot(x, pdf, color="orange", linewidth=1.5)
    ax.vlines(x=scipy.stats.lognorm.ppf(norm.cdf(2), s, loc, scale), ymin=ymin, ymax=ymax, color="orange", linewidth=1.5, linestyle="--")

    # alpha, beta, loc, scale = scipy.stats.beta.fit(times_trimmed, floc=l, fscale=r-l)
    # pdf = scipy.stats.beta.pdf(x, alpha, beta, loc, scale)
    # ax.plot(x, pdf, label="Beta", color="#f0f")
    # ax.vlines(x=scipy.stats.beta.ppf(norm.cdf(s), alpha, beta, loc, scale), ymin=ymin, ymax=ymax, color="#f0f", linewidth=2)

    # a, c, loc, scale = scipy.stats.exponweib.fit(times_trimmed)
    # pdf = scipy.stats.exponweib.pdf(x, a, c, loc, scale)
    # ax.plot(x, pdf, label="Exponetiated Weibull", color="#f0f")
    # ax.vlines(x=scipy.stats.exponweib.ppf(norm.cdf(s), a, c, loc, scale), ymin=ymin, ymax=ymax, color="#f0f", linewidth=2)
    
    # loc, scale = times_trimmed.median(), 1.48*f_mad(times_trimmed)
    # pdf = scipy.stats.norm.pdf(x, loc, scale)
    # ax.plot(x, pdf, label="Gaussian", color="#00e")
    # ax.vlines(x=scipy.stats.norm.ppf(norm.cdf(s), loc, scale), ymin=ymin, ymax=ymax, color="#00e", linewidth=2)
    

    # ax.vlines(x=times_trimmed.quantile(norm.cdf(s)), ymin=ymin, ymax=ymax, color="grey", linewidth=2, linestyle="--")
    # ax.vlines(x=min(times), ymin=ymin, ymax=ymax, color="grey", linewidth=2, linestyle="--")
    # ax.legend(loc="upper left")

# for ax in axes:
#     ax.set_xlim(left=left_lim, right=right_lim)

plt.show()

def trim2(y):
    return pandas.Series(y)

def trim(y, kl = 1, kr = 6):
    y = pandas.Series(y)
    m = y.mean()
    a = y.std()
    return y[(y >= (m-kl*a)) & (y <= (m+kr*a))]

def trim2(y, kl = 5, kr = 15):
    y = pandas.Series(y)
    m = y.median()
    a = f_mad(y)
    return y[(y >= (m-kl*a)) & (y <= (m+kr*a))]

def plot_fit(data, ax):
    data = pandas.Series(data)
    y = data
    y = trim(y, 1, 8)
    sns.kdeplot(y, fill=True, bw_adjust=0.5, color="mediumpurple", edgecolor="none", ax=ax)
    x = numpy.linspace(min(y), max(y), 500)
    gmm = GaussianMixture(n_components=2).fit(y.to_numpy().reshape(-1, 1))
    pdf = numpy.exp(gmm.score_samples(x.reshape(-1, 1)))
    # ax.plot(x, pdf, color="purple", linewidth=2)

    s, loc, scale = scipy.stats.lognorm.fit(data)
    pdf = scipy.stats.lognorm.pdf(x, s, loc, scale)
    ax.plot(x, pdf, color="orange", linewidth=2)
    print(f"lognorm.loc={loc:.2f}")

    ymin, ymax = ax.get_ylim()
    ymax *= 0.80
    pp = 0.95
    ppf = scipy.stats.lognorm.ppf(pp, s, loc, scale)
    ax.vlines(x=data.quantile(pp), ymin=ymin, ymax=ymax, color="purple", linewidth=1.5, linestyle="-")
    ax.vlines(x=y.quantile(pp), ymin=ymin, ymax=ymax, color="purple", linewidth=1.5, linestyle="--")
    # ax.vlines(x=ppf, ymin=ymin, ymax=ymax/0.8, color="orange", linewidth=1.5, linestyle="--")
    ax.vlines(x=y.mean()+norm.ppf(pp)*y.std(), ymin=ymin, ymax=ymax, color="red", linewidth=1.5, linestyle="--")
    ax.vlines(x=data.mean()+norm.ppf(pp)*data.std(), ymin=ymin, ymax=ymax, color="red", linewidth=1.5, linestyle="-")
    ax.vlines(x=data.mean()+norm.ppf(pp)*1.4826*f_mad(data), ymin=ymin, ymax=ymax, color="blue", linewidth=1.5, linestyle="-")
    ax.vlines(x=y.mean()+norm.ppf(pp)*1.4826*f_mad(y), ymin=ymin, ymax=ymax, color="blue", linewidth=1.5, linestyle="--")
    # ax.vlines(x=scale*numpy.exp(s*norm.ppf(pp))+loc, ymin=ymin, ymax=ymax, color="red", linewidth=5, linestyle="-")

fig = plt.figure(constrained_layout=True)
fig.set_size_inches(22, 10)
gs = gridspec.GridSpec(1, 2, figure=fig)
ax_left = fig.add_subplot(gs[0, 0])
ax_right = fig.add_subplot(gs[0, 1])
plot_fit(times_sock[0], ax_left)
plot_fit(times_sock[1], ax_right)
plt.show()
