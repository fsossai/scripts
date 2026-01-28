import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# For ridgeline plots
try:
    import joypy
except ImportError:
    raise ImportError("Please install the 'joypy' package: pip install joypy")

# Helper to format minutes as months:days:hours
def minutes_to_mdh(minutes):
    total_days = int(minutes) // (24 * 60)
    months = total_days // 30
    days = total_days % 30
    hours = (int(minutes) % (24 * 60)) // 60
    return f"{months}m {days}d {hours}h"

# Helper to format minutes as total days (with one decimal)
def minutes_to_days(minutes):
    return f"{minutes / (24*60):.1f} days"

# Load CSV
csv_file = "hta.csv"
df = pd.read_csv(csv_file)

# Prepare data for ridgeline plot: one column per target
df_ridge = df.copy()
df_ridge['TargetPct'] = (df_ridge['Target'] - 1.0) * 100
df_ridge['TargetPct'] = df_ridge['TargetPct'].round(2)
df_ridge['TargetPct'] = pd.Categorical(df_ridge['TargetPct'], categories=sorted(df_ridge['TargetPct'].unique(), reverse=False), ordered=True)

# Compute global 95th percentile to limit horizontal extent of ridgelines
global_x95 = np.percentile(df_ridge['HittingTime'].dropna(), 95)

# --- Manual vertical ridgeline plot using matplotlib ---
import scipy.stats as stats

targets_sorted = df_ridge['TargetPct'].cat.categories
num_targets = len(targets_sorted)

fig, ax = plt.subplots(figsize=(8, 1.2 * num_targets))
colors = plt.cm.viridis(np.linspace(0, 1, num_targets))

yticks = []
ylabels = []
max_density = 0

for i, (target, color) in enumerate(zip(targets_sorted, colors)):
    subset = df_ridge[df_ridge['TargetPct'] == target]['HittingTime'].dropna().values
    if len(subset) < 2:
        continue
    # KDE
    kde = stats.gaussian_kde(subset)
    y = np.linspace(0, global_x95, 400)
    density = kde(y)
    # Normalize and offset for stacking
    density = density / density.max() * 0.8  # scale for visual separation
    offset = i
    ax.fill_betweenx(y, offset, offset + density, color=color, alpha=0.8)
    ax.plot(offset + density, y, color='black', lw=1, alpha=0.7)
    # Median and 90th percentile ticks
    median = np.median(subset)
    p90 = np.percentile(subset, 90)
    ax.hlines(median, offset + 0.0, offset + 0.95, color='red', lw=2, label='Median' if i == 0 else "", zorder=3)
    ax.hlines(p90, offset + 0.0, offset + 0.95, color='orange', lw=2, label='90th percentile' if i == 0 else "", zorder=3)
    yticks.append(offset + 0.4)
    ylabels.append(str(target))

ax.set_ylim(0, global_x95)
ax.set_xlim(-0.1, num_targets)
days_step = 20
max_days = int(global_x95 // (24*60)) + 1
ytick_days = np.arange(0, max_days + days_step, days_step)
ytick_vals = ytick_days * 24 * 60
ytick_vals = ytick_vals[ytick_vals <= global_x95]
ax.set_yticks(ytick_vals)
ax.set_yticklabels([
    f"{minutes_to_mdh(y)}\n({minutes_to_days(y)})" for y in ytick_vals
])
ax.yaxis.grid(True, which='major', linestyle='--', color='gray', alpha=0.5)
ax.set_xticks(np.arange(num_targets) + 0.4)
ax.set_xticklabels(ylabels)
ax.set_xlabel("Target Percentage (%)")
ax.set_ylabel("Hitting Time (months:days:hours)\nand total days")
ax.set_title("Hitting Time Analysis (Vertical Ridgeline)")
ax.legend(loc='upper right')
plt.tight_layout()
plt.show()
