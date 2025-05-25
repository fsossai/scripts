from scipy.stats import norm
import numpy
import re

available = {
    "std", "pX", "rstdX", "mad", "range", "iqr"
}

def compute_mad(x):
    return (x - x.median()).abs().median()

def lower(y, spread_measure):
    n = re.search(r"\d+(\.\d+)?", spread_measure)
    if spread_measure.startswith("std"):
        coeff = float(n.group())
        return y.mean() - coeff * y.std()
    elif spread_measure.startswith("p"):
        p = float(n.group()) / 100.0
        return y.quantile(p)
    elif spread_measure.startswith("rstd"):
        coeff = float(n.group())
        return y.mean() - coeff * (1 / norm.ppf(0.75)) * y.apply(compute_mad)
    elif spread_measure == "mad":
        return y.median() - y.apply(compute_mad)
    elif spread_measure == "range":
        return y.min()
    elif spread_measure == "iqr":
        return y.quantile(0.25)

def upper(y, spread_measure):
    n = re.search(r"\d+(\.\d+)?", spread_measure)
    if spread_measure.startswith("std"):
        coeff = float(n.group())
        return y.mean() + coeff * y.std()
    elif spread_measure.startswith("p"):
        p = float(n.group()) / 100.0
        return y.quantile(1-p)
    elif spread_measure.startswith("rstd"):
        coeff = float(n.group())
        return y.mean() + coeff * (1 / norm.ppf(0.75)) * y.apply(compute_mad)
    elif spread_measure == "mad":
        return y.median() + y.apply(compute_mad)
    elif spread_measure == "range":
        return y.max()
    elif spread_measure == "iqr":
        return y.quantile(0.75)

def draw(ax, spread_measures, x, y, color, style):
    for i, sm in enumerate(spread_measures):
        y_lower = lower(y, sm)
        y_upper = upper(y, sm)
        if style == "area":
            alphas = numpy.linspace(0.15, 0.05, len(spread_measures))
        elif style == "bar":
            alphas = numpy.linspace(0.30, 0.10, len(spread_measures))
        if style == "area":
            ax.fill_between(x, y_lower, y_upper, interpolate=True, color=color, alpha=alphas[i])
        elif style == "bar":
            ax.vlines(x=x, ymin=ymin, ymax=ymax, color=color, alpha=alpha, linewidth=4)
