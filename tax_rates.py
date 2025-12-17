
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Data from
# https://taxfoundation.org/data/all/federal/2026-tax-brackets/

tax_data = [
    {
        "year": 2023,
        "brackets": [0, 11000, 44725, 95375, 182100, 231250, 578125, 1_000_000],
        "rates":    [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],
        "color": "green"
    },
    {
        "year": 2024,
        "brackets": [0, 11600, 47150, 100525, 191950, 243725, 609350, 1_000_000],
        "rates":    [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],
        "color": "red"
    },
    {
        "year": 2025,
        "brackets": [0, 11925, 48475, 103350, 197300, 250525, 626350, 1_000_000],
        "rates":    [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],
        "color": "orange"
    },
    {
        "year": 2026,
        "brackets": [0, 12400, 50400, 105700, 201775, 256225, 640600, 1_000_000],
        "rates":    [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],
        "color": "blue"
    },
]

def total_tax(income, brackets, rates):
    tax = 0
    for i, rate in enumerate(rates):
        lower, upper = brackets[i], brackets[i+1]
        if income > lower:
            tax += (min(income, upper) - lower) * rate
    return tax

incomes = np.linspace(0, 1_000_000, 1200)

# Calculate effective rates for each year
for year_data in tax_data:
    year_data["effective_rate"] = np.divide(
        [total_tax(x, year_data["brackets"], year_data["rates"]) for x in incomes],
        incomes,
        out=np.zeros_like(incomes),
        where=incomes>0
    )

fig, ax = plt.subplots(figsize=(10,6))
for year_data in tax_data:
    ax.plot(
        incomes,
        year_data["effective_rate"],
        color=year_data["color"],
        linewidth=2,
        label=str(year_data["year"])
    )

# Set major x-ticks every 100k and minor x-ticks every 50k, with labels for both
major_tick = 100_000
minor_tick = 50_000
major_xticks = np.arange(0, 1_000_001, major_tick)
minor_xticks = np.arange(0, 1_000_001, minor_tick)
all_xticks = np.unique(np.concatenate((major_xticks, minor_xticks)))
labels = []
for x in all_xticks:
    if x % major_tick == 0:
        labels.append(f"{int(x//1000)}k" if x < 1_000_000 else "1M")
    else:
        labels.append(f"{int(x//1000)}k")
ax.set_xticks(all_xticks)
ax.set_xticklabels(labels, rotation=30, ha='right')
ax.set_xlim(0, 1_000_000)
ax.tick_params(axis='x', which='minor', labelsize=8)
ax.set_xticks(minor_xticks, minor=True)

# Thicker grid for major, thinner for minor
ax.grid(True, which='major', axis='x', linestyle='-', linewidth=1.2, alpha=0.5)
ax.grid(True, which='minor', axis='x', linestyle='-', linewidth=0.5, alpha=0.3)

ax.set_title("Effective Federal Tax Rate (Single Filer, 2023-2026)")
ax.set_xlabel("Taxable Income ($)")
ax.set_ylabel("Effective Tax Rate (%)")
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0, decimals=0))
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_ylim(0, 0.40)
ax.legend()
fig.tight_layout()
plt.show()

