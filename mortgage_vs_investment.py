#!/usr/bin/env python3
"""
Mortgage vs Investment Analysis

Compares the cost of taking a mortgage versus investing the loan amount
and withdrawing monthly payments.

Shows:
1. Cumulative mortgage payments (principal + interest) over time
2. Investment portfolio value when starting with loan amount and withdrawing payments
3. Net difference (investment value - cumulative payments)
"""

import numpy as np
import matplotlib.pyplot as plt

def calculate_monthly_payment(P0, annual_rate, years):
    """Calculate fixed monthly payment for mortgage."""
    r_m = annual_rate / 12
    n = years * 12
    
    if r_m == 0:
        return P0 / n
    
    M = P0 * r_m * (1 + r_m)**n / ((1 + r_m)**n - 1)
    return M

def simulate_mortgage_cumulative(P0, annual_rate, years):
    """
    Simulate mortgage and return cumulative payments.
    
    Returns:
        months: array of month numbers
        cumulative_payments: total paid up to each month
        monthly_payment: fixed monthly payment amount
    """
    r_m = annual_rate / 12
    n = years * 12
    M = calculate_monthly_payment(P0, annual_rate, years)
    
    months = np.arange(n + 1)
    cumulative_payments = months * M
    
    return months, cumulative_payments, M

def simulate_investment_with_withdrawals(P0, monthly_payment, annual_return, years):
    """
    Simulate investment portfolio with monthly withdrawals.
    
    Start with P0, earn monthly compounded returns, withdraw monthly_payment each month.
    
    Returns:
        months: array of month numbers
        portfolio_value: remaining investment value each month
    """
    r_m = annual_return / 12
    n = years * 12
    
    months = np.arange(n + 1)
    portfolio_value = np.zeros(n + 1)
    portfolio_value[0] = P0
    
    for k in range(1, n + 1):
        # Investment grows
        new_value = portfolio_value[k-1] * (1 + r_m)
        # Withdraw payment
        new_value -= monthly_payment
        # Can't go negative
        portfolio_value[k] = max(0, new_value)
    
    return months, portfolio_value

def plot_mortgage_vs_investment():
    """Create comprehensive mortgage vs investment comparison plot."""
    
    # Parameters
    P0 = 300000  # $300,000 loan/investment
    years = 25   # 25-year term
    
    mortgage_rates = [0.02, 0.03, 0.04]
    investment_returns = [0.07, 0.08, 0.09]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Color schemes
    mortgage_colors = ['#1f77b4', '#2ca02c', '#d62728']  # Blue, green, red
    investment_colors = ['#ff7f0e', '#9467bd', '#8c564b']  # Orange, purple, brown
    net_colors = ['#e377c2', '#7f7f7f', '#bcbd22']  # Pink, gray, olive
    
    # Store data for legend ordering
    lines = []
    labels = []
    
    # Calculate all mortgage payments first
    mortgage_data = {}
    print("Calculating mortgage scenarios...")
    for i, rate in enumerate(mortgage_rates):
        months, cumulative, M = simulate_mortgage_cumulative(P0, rate, years)
        mortgage_data[rate] = {'months': months, 'cumulative': cumulative, 'payment': M}
        line, = ax.plot(months, cumulative / 1000, linewidth=3, 
                       color=mortgage_colors[i], linestyle='-',
                       label=f'Mortgage {rate*100:.0f}% (${M:,.0f}/mo)')
        lines.append(line)
        labels.append(f'Mortgage {rate*100:.0f}% (${M:,.0f}/mo)')
        print(f"  {rate*100:.0f}% mortgage: ${M:,.2f}/month → Total: ${cumulative[-1]:,.2f}")
    
    # Plot investment portfolios - one for each mortgage rate
    print("\nCalculating investment scenarios...")
    print("(Each investment uses withdrawal matching corresponding mortgage rate)")
    
    # Create investment scenarios matching each mortgage rate
    for mort_idx, mort_rate in enumerate(mortgage_rates):
        M_mort = mortgage_data[mort_rate]['payment']
        
        for inv_idx, inv_ret in enumerate(investment_returns):
            months, portfolio = simulate_investment_with_withdrawals(P0, M_mort, inv_ret, years)
            
            # Use different line styles/transparency for different mortgage rates
            alpha = 0.4 + (mort_idx * 0.3)  # Vary transparency
            line, = ax.plot(months, portfolio / 1000, linewidth=2, 
                           color=investment_colors[inv_idx], linestyle='--',
                           alpha=alpha,
                           label=f'Inv {inv_ret*100:.0f}% w/ {mort_rate*100:.0f}% payment (${M_mort:,.0f}/mo)')
            lines.append(line)
            labels.append(f'Inv {inv_ret*100:.0f}% w/ {mort_rate*100:.0f}% payment (${M_mort:,.0f}/mo)')
            
            final_value = portfolio[-1]
            depletion = "DEPLETED" if final_value < 1 else f"${final_value:,.2f} remaining"
            print(f"  {inv_ret*100:.0f}% return w/ {mort_rate*100:.0f}% payment: {depletion}")
    
    # Plot net difference for each (mortgage, investment) pair - focus on diagonal comparisons
    print("\nCalculating net differences...")
    
    for idx, (mort_rate, inv_ret) in enumerate(zip(mortgage_rates, investment_returns)):
        months_mort = mortgage_data[mort_rate]['months']
        cumulative_mort = mortgage_data[mort_rate]['cumulative']
        M_mort = mortgage_data[mort_rate]['payment']
        
        months_inv, portfolio_inv = simulate_investment_with_withdrawals(P0, M_mort, inv_ret, years)
        net_difference = portfolio_inv - cumulative_mort
        line, = ax.plot(months_mort, net_difference / 1000, linewidth=2.5, 
                       color=net_colors[idx], linestyle=':',
                       label=f'Net: {inv_ret*100:.0f}% inv − {mort_rate*100:.0f}% mort')
        lines.append(line)
        labels.append(f'Net: {inv_ret*100:.0f}% inv − {mort_rate*100:.0f}% mort')
        print(f"  {inv_ret*100:.0f}% inv vs {mort_rate*100:.0f}% mort: Final net = ${net_difference[-1]:,.2f}")
    
    # Add zero line for reference
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    # Add horizontal line at $300,000 (y=300 in $1000s)
    ax.axhline(y=300, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='$300,000 reference')
    
    # Formatting
    ax.set_xlabel('Time (months)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Value ($1000s)', fontsize=14, fontweight='bold')
    ax.set_title(f'Mortgage vs Investment Analysis\n' + 
                 f'Loan/Investment: ${P0:,.0f} | Term: {years} years | ' +
                 f'Each investment scenario withdraws payment matching its mortgage rate',
                 fontsize=16, fontweight='bold', pad=20)
    
    # Legend with three columns
    ax.legend(handles=lines, labels=labels, fontsize=10, loc='upper left', 
             ncol=1, framealpha=0.95, edgecolor='black')
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, years * 12)
    
    # Add annotations
    ax.text(0.98, 0.02, 
            'Solid lines: Cumulative mortgage payments\n' +
            'Dashed lines: Investment portfolio value\n' +
            'Dotted lines: Net difference (investment − payments)',
            transform=ax.transAxes, fontsize=9, verticalalignment='bottom',
            horizontalalignment='right', bbox=dict(boxstyle='round', 
            facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('mortgage_vs_investment.png', dpi=150, bbox_inches='tight')
    return fig

def print_detailed_analysis():
    """Print detailed comparison analysis."""
    P0 = 300000
    years = 25
    
    print("=" * 90)
    print("MORTGAGE vs INVESTMENT ANALYSIS")
    print("=" * 90)
    print(f"\nScenario: ${P0:,.0f} loan amount / initial investment, {years}-year term")
    print(f"\nAssumptions:")
    print(f"  • Mortgage: Standard amortization with monthly compounding")
    print(f"  • Investment: Start with ${P0:,.0f}, earn monthly compounded returns,")
    print(f"    withdraw monthly mortgage payment each month")
    
    print("\n" + "─" * 90)
    print("MORTGAGE SCENARIOS")
    print("─" * 90)
    print(f"{'Rate':<8} {'Monthly':<14} {'Total Paid':<16} {'Total Interest':<16}")
    print("─" * 90)
    
    mortgage_rates = [0.02, 0.03, 0.04]
    mortgage_data = {}
    
    for rate in mortgage_rates:
        M = calculate_monthly_payment(P0, rate, years)
        total = M * 12 * years
        interest = total - P0
        mortgage_data[rate] = {'payment': M, 'total': total, 'interest': interest}
        print(f"{rate*100:<8.1f}% ${M:<13,.2f} ${total:<15,.2f} ${interest:<15,.2f}")
    
    print("\n" + "─" * 90)
    print("INVESTMENT SCENARIOS (using 3% mortgage payment)")
    print("─" * 90)
    
    ref_payment = mortgage_data[0.03]['payment']
    print(f"Monthly withdrawal: ${ref_payment:,.2f}")
    print(f"\n{'Return':<8} {'Final Value':<20} {'Status':<30}")
    print("─" * 90)
    
    investment_returns = [0.07, 0.08, 0.09]
    
    for ret in investment_returns:
        _, portfolio = simulate_investment_with_withdrawals(P0, ref_payment, ret, years)
        final_value = portfolio[-1]
        
        if final_value < 1:
            # Find when it depleted
            depletion_month = np.argmax(portfolio <= 0)
            depletion_years = depletion_month / 12
            status = f"Depleted after {depletion_years:.1f} years"
            value_str = "$0.00"
        else:
            status = f"${final_value:,.2f} remaining"
            value_str = f"${final_value:,.2f}"
        
        print(f"{ret*100:<8.1f}% {value_str:<20} {status:<30}")
    
    print("\n" + "─" * 90)
    print("NET BENEFIT: Investment Value - Cumulative Mortgage Payments")
    print("─" * 90)
    print(f"{'Mortgage':<10} {'Investment':<12} {'Final Net':<20} {'Interpretation':<30}")
    print("─" * 90)
    
    for mort_rate in [0.03]:  # Focus on 3% mortgage
        _, cumulative, M = simulate_mortgage_cumulative(P0, mort_rate, years)
        total_paid = cumulative[-1]
        
        for inv_ret in investment_returns:
            _, portfolio = simulate_investment_with_withdrawals(P0, M, inv_ret, years)
            net = portfolio[-1] - total_paid
            
            if net > 0:
                interpretation = f"Investment wins by ${net:,.2f}"
            elif net < 0:
                interpretation = f"Mortgage costs ${-net:,.2f} more"
            else:
                interpretation = "Break even"
            
            print(f"{mort_rate*100:<10.1f}% {inv_ret*100:<12.1f}% ${net:<19,.2f} {interpretation:<30}")
    
    print("\n" + "=" * 90)
    print("KEY INSIGHTS:")
    print("=" * 90)
    print("• If investment return > mortgage rate: Investing the lump sum can be advantageous")
    print("• If investment return < mortgage rate: Direct mortgage payment is better")
    print("• Risk: Investments are volatile; mortgages are fixed obligations")
    print("• The 'net' curves show cumulative benefit/cost of the investment strategy")
    print("• Negative net means you've paid more through withdrawals than mortgage would cost")
    print("=" * 90)

if __name__ == "__main__":
    print_detailed_analysis()
    print("\nGenerating plot...")
    plot_mortgage_vs_investment()
    print("\nPlot saved as 'mortgage_vs_investment.png'")
    plt.show()
