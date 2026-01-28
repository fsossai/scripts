import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider
import numpy as np
import sys
import json

def main():
    try:
        with open('output.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: output.json not found. Please run the simulation first.")
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
            'TimeLimitWait': params['timeLimitWait'],
            'CAGR': (params['cagr'] - 1.0) * 100.0
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
    
    plt.subplots_adjust(bottom=0.25, wspace=0.1)

    # plot placeholders
    surf = [None] 
    the_table = [None] 

    ax.set_xlabel('Target Open (%)')
    ax.set_ylabel('Target Close (%)')
    ax.set_zlabel('CAGR (%)')
    ax.set_title('CAGR (%) Surface')

    # Sliders
    # Get unique sorted values to snap to
    hold_values = sorted(df['TimeLimitHold'].unique())
    wait_values = sorted(df['TimeLimitWait'].unique())

    ax_hold = plt.axes([0.15, 0.1, 0.35, 0.03])
    ax_wait = plt.axes([0.15, 0.05, 0.35, 0.03])

    # Sliders operate on INDEX of the values array
    s_hold = Slider(ax_hold, 'Max Hold Days', 0, len(hold_values) - 1, valinit=len(hold_values)-1, valstep=1)
    s_wait = Slider(ax_wait, 'Max Wait Days', 0, len(wait_values) - 1, valinit=len(wait_values)-1, valstep=1)

    def format_slider_label(slider, values):
        idx = int(slider.val)
        return f"{values[idx]:.2f}"

    def update_plot(val=None):
        if surf[0]:
            surf[0].remove()
        
        # Get values from indices
        hold_idx = int(s_hold.val)
        wait_idx = int(s_wait.val)
        
        max_hold = hold_values[hold_idx]
        max_wait = wait_values[wait_idx]

        # Update slider text
        s_hold.valtext.set_text(format_slider_label(s_hold, hold_values))
        s_wait.valtext.set_text(format_slider_label(s_wait, wait_values))

        # --- Update 3D Surface ---
        Z_masked = Z.copy()
        mask_indices = (Hold_Grid > max_hold) | (Wait_Grid > max_wait)
        Z_masked[mask_indices] = np.nan
        
        surf[0] = ax.plot_surface(X, Y, Z_masked, cmap='viridis', edgecolor='none')
        ax.set_zlim(np.nanmin(Z), np.nanmax(Z))

        # --- Update Table ---
        # Filter DataFrame
        filtered_df = df[(df['TimeLimitHold'] <= max_hold) & (df['TimeLimitWait'] <= max_wait)]
        
        # Sort by CAGR (Desc) -> Top Strategies
        top_df = filtered_df.sort_values(by='CAGR', ascending=False).head(15)

        cell_text = []
        for index, row in top_df.iterrows():
            cell_text.append([
                f"{row['TargetOpen']:.2f}",
                f"{row['TargetClose']:.2f}",
                f"{row['TimeLimitHold']:.2f}",
                f"{row['TimeLimitWait']:.2f}",
                f"{row['CAGR']:.4f}"
            ])
        
        headers = ['T.Open', 'T.Close', 'MaxHold', 'MaxWait', 'CAGR %']
        
        if the_table[0]:
            the_table[0].remove()
            
        the_table[0] = ax_table.table(
            cellText=cell_text, 
            colLabels=headers, 
            loc='center', 
            cellLoc='center',
            bbox=[0, 0, 1, 1]
        )
        the_table[0].auto_set_font_size(False)
        the_table[0].set_fontsize(10)
        ax_table.set_title(f"Top {len(top_df)} Strategies (Filtered)")

    s_hold.on_changed(update_plot)
    s_wait.on_changed(update_plot)

    # First draw
    update_plot()

    plt.show()

if __name__ == "__main__":
    main()
