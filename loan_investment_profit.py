#!/usr/bin/env python3
"""
Loan Investment Strategy Simulation

Simulates the scenario:
1. Take a loan at interest rate R_L
2. Immediately invest the loan amount at return rate R_i
3. Each month, withdraw only the loan payment amount from the investment
4. Calculate cumulative profit: investment value - cumulative payments made

Tests multiple (R_L, R_i) combinations and plots profit over time.
"""

import numpy as np
import matplotlib.pyplot as plt
from itertools import product

def calculate_monthly_payment(principal, annual_rate, years):
    """Calculate fixed monthly payment for amortized loan."""
    r_m = annual_rate / 12
    n = years * 12
    
    if r_m == 0:
        return principal / n
    
    payment = principal * r_m * (1 + r_m)**n / ((1 + r_m)**n - 1)
    return payment

def simulate_loan_investment_strategy(principal, loan_rate, investment_rate, years):
    """
    Simulate loan + investment strategy.
    
    Args:
        principal: Loan amount (and initial investment)
        loan_rate: Annual loan interest rate
        investment_rate: Annual investment return rate
        years: Loan duration in years
    
    Returns:
        months: Array of month numbers
        investment_value: Investment portfolio value each month
        cumulative_payments: Total amount paid to loan up to each month
        profit: Investment value - cumulative payments (net position)
        monthly_payment: Fixed monthly loan payment
    """
    n = years * 12  # Total months
    r_inv = investment_rate / 12  # Monthly investment return
    
    # Calculate fixed monthly loan payment
    monthly_payment = calculate_monthly_payment(principal, loan_rate, years)
    
    # Initialize arrays
    months = np.arange(n + 1)
    investment_value = np.zeros(n + 1)
    cumulative_payments = np.zeros(n + 1)
    
    # Initial conditions
    investment_value[0] = principal
    cumulative_payments[0] = 0
    
    # Simulate month by month
    for k in range(1, n + 1):
        # Investment grows with returns
        investment_value[k] = investment_value[k-1] * (1 + r_inv)
        
        # Withdraw monthly payment
        investment_value[k] -= monthly_payment
        
        # Can't go negative
        investment_value[k] = max(0, investment_value[k])
        
        # Accumulate payments
        cumulative_payments[k] = cumulative_payments[k-1] + monthly_payment
    
    # Profit = what you have - what you paid
    profit = investment_value - cumulative_payments
    
    return months, investment_value, cumulative_payments, profit, monthly_payment

def plot_profit_analysis(principal, loan_rates, investment_rates, years):
    """
    Generate comprehensive profit analysis for multiple rate combinations.
    
    Args:
        principal: Loan amount
        loan_rates: List of loan interest rates to test
        investment_rates: List of investment return rates to test
        years: Loan duration in years
    """
    fig, ax1 = plt.subplots(1, 1, figsize=(14, 8))
    
    # Color map for different combinations
    colors = plt.cm.tab10(np.linspace(0, 1, len(loan_rates) * len(investment_rates)))
    
    print("=" * 80)
    print(f"LOAN INVESTMENT STRATEGY SIMULATION")
    print("=" * 80)
    print(f"Principal: ${principal:,.2f}")
    print(f"Loan Duration: {years} years ({years*12} months)")
    print(f"\nTesting {len(loan_rates)} loan rates × {len(investment_rates)} investment rates")
    print("=" * 80)
    
    # Store results for summary
    results = []
    
    color_idx = 0
    for r_loan in loan_rates:
        for r_inv in investment_rates:
            months, inv_value, cum_payments, profit, monthly_payment = \
                simulate_loan_investment_strategy(principal, r_loan, r_inv, years)
            
            years_timeline = months / 12
            
            # Calculate key metrics
            final_profit = profit[-1]
            max_profit = np.max(profit)
            min_profit = np.min(profit)
            breakeven_months = np.where(profit > 0)[0]
            
            if len(breakeven_months) > 0:
                first_positive = breakeven_months[0]
            else:
                first_positive = None
            
            # Store results
            results.append({
                'r_loan': r_loan,
                'r_inv': r_inv,
                'monthly_payment': monthly_payment,
                'final_profit': final_profit,
                'max_profit': max_profit,
                'min_profit': min_profit,
                'breakeven_month': first_positive
            })
            
            # Label for this combination
            label = f'L={r_loan*100:.1f}%, I={r_inv*100:.1f}%'
            color = colors[color_idx]
            
            # Plot: Cumulative Profit over time
            ax1.plot(years_timeline, profit / 1000, linewidth=2.5, 
                    color=color, label=label, alpha=0.8)
            
            color_idx += 1
            
            # Print summary for this combination
            status = "PROFIT" if final_profit > 0 else "LOSS"
            print(f"\nL={r_loan*100:.1f}%, I={r_inv*100:.1f}% | Payment: ${monthly_payment:,.2f}/mo")
            print(f"  Final profit: ${final_profit:,.2f} ({status})")
            print(f"  Peak profit: ${max_profit:,.2f} | Min profit: ${min_profit:,.2f}")
    
    # Format Plot: Cumulative Profit
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax1.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Cumulative Profit ($1000s)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Cumulative Profit Over Time\n' +
                  f'(Investment Value - Cumulative Payments)\n' +
                  f'Principal: ${principal:,.0f}, Duration: {years} years',
                  fontsize=14, fontweight='bold', pad=15)
    ax1.legend(fontsize=9, loc='best', ncol=2, framealpha=0.95)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(0, years)
    
    # Add annotations
    ax1.text(0.02, 0.98, 
            'Profit = Investment Value - Cumulative Payments\n' +
            'Positive profit: Investment strategy wins\n' +
            'Negative profit: Direct loan payment better',
            transform=ax1.transAxes, fontsize=9, 
            verticalalignment='top', bbox=dict(boxstyle='round', 
            facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('loan_investment_profit.png', dpi=150, bbox_inches='tight')
    
    # Print summary table
    print("\n" + "=" * 80)
    print("FINAL RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'Loan Rate':<12} {'Inv Rate':<12} {'Payment':<14} {'Final Profit':<18} {'Status':<10}")
    print("-" * 80)
    
    for r in results:
        status = "WIN ✓" if r['final_profit'] > 0 else "LOSS ✗"
        print(f"{r['r_loan']*100:<12.1f}% {r['r_inv']*100:<12.1f}% "
              f"${r['monthly_payment']:<13,.2f} ${r['final_profit']:<17,.2f} {status:<10}")
    
    print("=" * 80)
    
    # Find best and worst combinations
    best = max(results, key=lambda x: x['final_profit'])
    worst = min(results, key=lambda x: x['final_profit'])
    
    print(f"\nBEST COMBINATION:")
    print(f"  Loan {best['r_loan']*100:.1f}%, Investment {best['r_inv']*100:.1f}%")
    print(f"  Final Profit: ${best['final_profit']:,.2f}")
    
    print(f"\nWORST COMBINATION:")
    print(f"  Loan {worst['r_loan']*100:.1f}%, Investment {worst['r_inv']*100:.1f}%")
    print(f"  Final Profit: ${worst['final_profit']:,.2f}")
    
    print("\n" + "=" * 80)
    
    return fig, results

def main():
    """Main execution function."""
    
    # ========== CONFIGURATION ==========
    # Easy to modify parameters
    PRINCIPAL = 100000      # Loan amount in dollars
    YEARS = 30              # Loan duration in years
    
    # Test multiple loan rates and investment rates
    LOAN_RATES = [0.03, 0.04, 0.05]           # 3%, 4%, 5%
    INVESTMENT_RATES = [0.06, 0.07, 0.08]     # 6%, 7%, 8%
    
    # ===================================
    
    # Run simulation
    fig, results = plot_profit_analysis(PRINCIPAL, LOAN_RATES, INVESTMENT_RATES, YEARS)
    
    print("\nPlot saved as 'loan_investment_profit.png'")
    plt.show()

if __name__ == "__main__":
    main()
