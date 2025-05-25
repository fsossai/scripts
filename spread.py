from scipy.stats import norm
import re

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
