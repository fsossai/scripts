from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np

init = 10000 # initial amount [$]
spm = 430 # savings per month [$]
ir = 3.75 # interest rate [%]
years = 5 # number of years to simulate

r = ir / 100
savings = init + spm * 12 *years

days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

total = init
for iyear in range(years):
    for imonth in range(12):
        for iday in range(days_in_month[imonth]):
            total *= 1 + r/365
        total += spm
    print(f"End of year {iyear+1:3} : {total:13.2f} $")
print()

ir_init = np.power(np.exp(r), years)
ir_spm = (np.exp(r / 12) * (np.exp(r*years) - 1)) / (np.exp(r / 12) - 1)
# correction: this term represents the interest generated if the savings-per-month
# would start at the beginning of the cycle (i.e. month)
ir_spm -= (np.exp(r*years) - 1)

from_init = init * ir_init
from_spm = spm * ir_spm

total_pred = from_init + from_spm
interests_pred = total_pred - savings
interests = total - savings
ratio = interests / savings
ratio_pred = interests_pred / savings

print(f"Savings                     : {savings:13.2f} $")
print()
print(f"Interests (actual $)        : {interests:13.2f} $")
print(f"Interests (actual %)        : {ratio*100:13.1f} %")
print()
print(f"Interests (prediction $)    : {interests_pred:13.2f} $")
print(f"Interests (prediction %)    : {ratio_pred*100:13.1f} %")

f = lambda y, r: spm*(np.exp(y*r)-1) / (np.exp(r/12)-1)
y = np.arange(1, years+1)
formatter = FuncFormatter(lambda x, _: f'{int(x/1000)}k')
plt.gca().yaxis.set_major_formatter(formatter)
plt.plot(y, init + y * spm * 12, "--", label="R=0%")
plt.plot(y, init + f(y, 0.03), label="R=3%")
plt.plot(y, init + f(y, 0.05), label="R=5%")
plt.plot(y, init + f(y, 0.07), label="R=7%")
plt.plot(y, init + f(y, 0.10), label="R=10%")
plt.xlabel("Time [years]")
plt.ylabel("Savings [$]")
plt.legend()
plt.grid(True)
plt.show()
