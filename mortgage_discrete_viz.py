#!/usr/bin/env python3
"""
Discrete-Time Mortgage Visualization

Visualizes monthly mortgage progression over 25 years at different interest rates.
Shows principal decay, payment breakdown, and cumulative interest.
"""

import numpy as np
import matplotlib.pyplot as plt

def calculate_monthly_payment(P0, annual_rate, years):
    """Calculate fixed monthly payment."""
    r_m = annual_rate / 12
    n = years * 12
    
    if r_m == 0:
        return P0 / n
    
    M = P0 * r_m * (1 + r_m)**n / ((1 + r_m)**n - 1)
    return M

def simulate_mortgage(P0, annual_rate, years):
    """
    Simulate month-by-month mortgage progression.
    
    Returns:
        months: array of month numbers
        principal: remaining principal each month
        interest_paid: interest portion of each payment
        principal_paid: principal portion of each payment
        cumulative_interest: total interest paid up to each month
    """
    r_m = annual_rate / 12
    n = years * 12
    M = calculate_monthly_payment(P0, annual_rate, years)
    
    months = np.arange(n + 1)
    principal = np.zeros(n + 1)
    interest_paid = np.zeros(n + 1)
    principal_paid = np.zeros(n + 1)
    cumulative_interest = np.zeros(n + 1)
    
    principal[0] = P0
    
    for k in range(1, n + 1):
        # Interest on current balance
        interest = principal[k-1] * r_m
        # Principal reduction
        principal_reduction = M - interest
        
        interest_paid[k] = interest
        principal_paid[k] = principal_reduction
        principal[k] = max(0, principal[k-1] - principal_reduction)
        cumulative_interest[k] = cumulative_interest[k-1] + interest
    
    return months, principal, interest_paid, principal_paid, cumulative_interest, M

def plot_mortgage_analysis():
    """Create comprehensive mortgage visualization."""
    
    P0 = 300000  # $300,000 loan
    years = 25
    rates = [0.02, 0.03, 0.04, 0.05]
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    fig.suptitle(f'Discrete-Time Mortgage Analysis: 25-Year Loan, ${P0:,.0f} Principal', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Remaining Principal Over Time
    ax1 = fig.add_subplot(gs[0, :])
    for rate, color in zip(rates, colors):
        months, principal, _, _, _, M = simulate_mortgage(P0, rate, years)
        years_timeline = months / 12
        ax1.plot(years_timeline, principal, linewidth=2.5, color=color, 
                label=f'{rate*100:.0f}% (M=${M:,.2f}/mo)')
    
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Remaining Principal ($)', fontsize=12)
    ax1.set_title('Remaining Principal vs Time', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, years)
    ax1.set_ylim(0, P0 * 1.05)
    
    # Plot 2: Monthly Payment Breakdown (stacked area for 5% rate)
    ax2 = fig.add_subplot(gs[1, 0])
    rate = 0.05
    months, _, interest_paid, principal_paid, _, M = simulate_mortgage(P0, rate, years)
    years_timeline = months / 12
    
    ax2.fill_between(years_timeline, 0, principal_paid, 
                     color='#2E86AB', alpha=0.7, label='Principal')
    ax2.fill_between(years_timeline, principal_paid, principal_paid + interest_paid, 
                     color='#C73E1D', alpha=0.7, label='Interest')
    ax2.plot(years_timeline, np.full_like(years_timeline, M), 
            'k--', linewidth=2, label=f'Total Payment (${M:.2f})')
    
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Monthly Payment ($)', fontsize=12)
    ax2.set_title(f'Payment Breakdown at {rate*100:.0f}% Rate', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, years)
    
    # Plot 3: Cumulative Interest Paid
    ax3 = fig.add_subplot(gs[1, 1])
    for rate, color in zip(rates, colors):
        months, _, _, _, cumulative_interest, _ = simulate_mortgage(P0, rate, years)
        years_timeline = months / 12
        total_interest = cumulative_interest[-1]
        ax3.plot(years_timeline, cumulative_interest / 1000, linewidth=2.5, color=color,
                label=f'{rate*100:.0f}% (Total: ${total_interest:,.0f})')
    
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Cumulative Interest Paid ($1000s)', fontsize=12)
    ax3.set_title('Total Interest Accumulation', fontsize=13, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, years)
    
    # Plot 4: Interest vs Principal Ratio
    ax4 = fig.add_subplot(gs[2, 0])
    for rate, color in zip(rates, colors):
        months, _, interest_paid, principal_paid, _, _ = simulate_mortgage(P0, rate, years)
        years_timeline = months / 12
        # Ratio of interest to principal in each payment
        ratio = np.divide(interest_paid, principal_paid, 
                         where=principal_paid>0, out=np.zeros_like(interest_paid))
        ax4.plot(years_timeline[1:], ratio[1:], linewidth=2.5, color=color,
                label=f'{rate*100:.0f}%')
    
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Interest / Principal Ratio', fontsize=12)
    ax4.set_title('Interest-to-Principal Ratio in Each Payment', fontsize=13, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=1, color='black', linestyle=':', linewidth=1, alpha=0.5)
    ax4.set_xlim(0, years)
    
    # Plot 5: Equity Build-up
    ax5 = fig.add_subplot(gs[2, 1])
    for rate, color in zip(rates, colors):
        months, principal, _, _, _, _ = simulate_mortgage(P0, rate, years)
        years_timeline = months / 12
        equity = P0 - principal
        equity_percent = 100 * equity / P0
        ax5.plot(years_timeline, equity_percent, linewidth=2.5, color=color,
                label=f'{rate*100:.0f}%')
    
    ax5.set_xlabel('Time (years)', fontsize=12)
    ax5.set_ylabel('Equity (%)', fontsize=12)
    ax5.set_title('Equity Build-up Over Time', fontsize=13, fontweight='bold')
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim(0, years)
    ax5.set_ylim(0, 100)
    
    plt.savefig('mortgage_discrete_analysis.png', dpi=150, bbox_inches='tight')
    return fig

def print_summary_table():
    """Print detailed comparison table."""
    P0 = 300000
    years = 25
    rates = [0.02, 0.03, 0.04, 0.05]
    
    print("=" * 80)
    print("DISCRETE-TIME MORTGAGE COMPARISON (25 Years, $300,000 Principal)")
    print("=" * 80)
    print(f"{'Rate':<8} {'Monthly':<12} {'Annual':<12} {'Total Paid':<14} {'Total Interest':<16} {'Interest/Principal':<10}")
    print(f"{'(%)':<8} {'Payment':<12} {'Payment':<12} {'($)':<14} {'($)':<16} {'Ratio':<10}")
    print("-" * 80)
    
    for rate in rates:
        M = calculate_monthly_payment(P0, rate, years)
        annual_payment = M * 12
        total_paid = M * 12 * years
        total_interest = total_paid - P0
        ratio = total_interest / P0
        
        print(f"{rate*100:<8.1f} ${M:<11,.2f} ${annual_payment:<11,.2f} ${total_paid:<13,.2f} ${total_interest:<15,.2f} {ratio:<10.3f}")
    
    print("=" * 80)
    
    # Additional insights
    print("\nKEY INSIGHTS:")
    print(f"  • At 2%, you pay ${calculate_monthly_payment(P0, 0.02, years) * 12 * years - P0:,.2f} in interest")
    print(f"  • At 5%, you pay ${calculate_monthly_payment(P0, 0.05, years) * 12 * years - P0:,.2f} in interest")
    
    interest_2 = calculate_monthly_payment(P0, 0.02, years) * 12 * years - P0
    interest_5 = calculate_monthly_payment(P0, 0.05, years) * 12 * years - P0
    extra = interest_5 - interest_2
    print(f"  • A 3% rate increase costs an extra ${extra:,.2f} over {years} years")
    
    # Crossover point where you've paid more interest than principal
    print("\n  TIME TO PAY 50% OF PRINCIPAL:")
    for rate in rates:
        months, principal, _, _, _, _ = simulate_mortgage(P0, rate, years)
        half_point = np.argmin(np.abs(principal - P0/2))
        years_to_half = half_point / 12
        print(f"    {rate*100:.0f}%: {years_to_half:.1f} years")
    
    print("=" * 80)

if __name__ == "__main__":
    print_summary_table()
    print("\nGenerating visualization...")
    plot_mortgage_analysis()
    print("Plot saved as 'mortgage_discrete_analysis.png'")
    plt.show()
