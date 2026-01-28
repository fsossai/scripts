import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import sys
import json

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <json_file>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

    # Flatten JSON to DataFrame for easy handling
    # We need: TargetOpen, TargetClose, TimeLimitHold, TimeLimitWait, Gain
    # Structure: item['parameters']['to'], etc.
    
    rows = []
    for item in data:
        params = item['parameters']
        rows.append({
            'TargetOpen': params['to'],
            'TargetClose': params['tc'],
            'TimeLimitHold': params['timeLimitHold'],
            'TimeLimitWait': params['timeLimitWait'],
            'CAGR': (params['cagr'] - 1.0) * 100.0,
            'NumOrders': params['numOrders']
        })
    
    df = pd.DataFrame(rows)

    # Prepare data for 3D plotting
    try:
        pivot_gain = df.pivot(index='TargetClose', columns='TargetOpen', values='CAGR')
        X_unique = np.sort(df['TargetOpen'].unique())
        Y_unique = np.sort(df['TargetClose'].unique())
        X, Y = np.meshgrid(X_unique, Y_unique)
        Z = pivot_gain.values
        
        # Parallel grids for TimeLimits to check constraints
        pivot_hold = df.pivot(index='TargetClose', columns='TargetOpen', values='TimeLimitHold')
        pivot_wait = df.pivot(index='TargetClose', columns='TargetOpen', values='TimeLimitWait')
        Hold_Grid = pivot_hold.values
        Wait_Grid = pivot_wait.values
    except Exception as e:
        print(f"Error processing data: {e}")
        sys.exit(1)

    # Initial plot
    fig = plt.figure(figsize=(16, 9))
    
    # 3D Plot Area
    ax = fig.add_subplot(121, projection='3d')
    
    # Table Area
    ax_table = fig.add_subplot(122)
    ax_table.axis('off')
    
    plt.subplots_adjust(bottom=0.05, wspace=0.1)

    ax.set_title('CAGR (%) Surface')

    # --- Draw 3D Surface ---
    # No masking needed as we show everything
    
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')
    # ax.set_zlim(np.nanmin(Z), np.nanmax(Z))

    # --- Draw Table ---
    # Sort by CAGR (Desc) -> Top Strategies across entire dataset
    top_df = df.sort_values(by='CAGR', ascending=False).head(15)

    cell_text = []
    for index, row in top_df.iterrows():
        cell_text.append([
            f"{row['TargetOpen']:.2f}",
            f"{row['TargetClose']:.2f}",
            f"{row['TimeLimitHold']:.2f}",
            f"{row['TimeLimitWait']:.2f}",
            f"{row['CAGR']:.2f}",
            f"{int(row['NumOrders'])}"
        ])
    
    headers = ['T.Open', 'T.Close', 'MaxHold', 'MaxWait', 'CAGR %', 'Orders']
    
    the_table = ax_table.table(
        cellText=cell_text, 
        colLabels=headers, 
        loc='center', 
        cellLoc='center',
        bbox=[0, 0, 1, 1]
    )
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(10)
    ax_table.set_title(f"Top {len(top_df)} Strategies")

    plt.show()

if __name__ == "__main__":
    main()
