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

    # Flatten JSON
    rows = []
    for entry in data:
        p = entry['parameters']
        rows.append({
            'Fast': p['fast'],
            'Slow': p['slow'],
            'CAGR': p['cagr'] * 100, # Convert to %
            'Orders': p['numOrders']
        })
    
    df = pd.DataFrame(rows)
    
    if df.empty:
        print("No data to plot.")
        return

    # Pivot for Surface Plot
    # We need a grid. Duplicate values for (Fast,Slow) should not exist in theory.
    pivot_df = df.pivot(index='Slow', columns='Fast', values='CAGR')
    
    X = pivot_df.columns.values # Fast
    Y = pivot_df.index.values   # Slow
    X, Y = np.meshgrid(X, Y)
    Z = pivot_df.values

    # Setup Plot
    fig = plt.figure(figsize=(14, 8))
    
    # --- 3D Surface ---
    ax = fig.add_subplot(121, projection='3d')
    ax.set_xlabel('Fast Window')
    ax.set_ylabel('Slow Window')
    ax.set_zlabel('CAGR (%)')
    ax.set_title('MAC Strategy: CAGR Surface')
    
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')
    # fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

    # --- Limit checks ---
    # Annotate max point
    max_idx = df['CAGR'].idxmax()
    best = df.loc[max_idx]
    
    ax.scatter([best['Fast']], [best['Slow']], [best['CAGR']], color='red', s=50, label='Max CAGR')
    ax.legend()
    
    # --- Best Config Table ---
    ax_table = fig.add_subplot(122)
    ax_table.axis('off')
    ax_table.set_title('Best Configuration')
    
    # Create table data
    # Sort by CAGR descending
    top_df = df.sort_values(by='CAGR', ascending=False).head(10)
    
    table_data = []
    headers = ['Fast', 'Slow', 'CAGR %', 'Orders']
    
    for _, row in top_df.iterrows():
        table_data.append([
            int(row['Fast']),
            int(row['Slow']),
            f"{row['CAGR']:.2f}",
            int(row['Orders'])
        ])
        
    table = ax_table.table(
        cellText=table_data,
        colLabels=headers,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)

    plt.tight_layout()
    print(f"Global Max CAGR: {best['CAGR']:.2f}% (Fast: {int(best['Fast'])}, Slow: {int(best['Slow'])})")
    plt.show()

if __name__ == "__main__":
    main()
