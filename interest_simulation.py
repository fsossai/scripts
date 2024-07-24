import numpy
import matplotlib.pyplot as plt

init = 0 # initial amount [$]
spm = 25 # savings per month [$]
ir = 4.50 # interest rate [%]
years = 5 # number of years to simulate

days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

r = ir/100
total = init
for iyear in range(years):
    for imonth in range(12):
        for iday in range(days_in_month[imonth]):
            total *= 1 + r/365
        total += spm
    print(f"End of year {iyear+1:3} : {total:13.2f} $")
print()

#f = 1 + (r/6 + 0.46)*r

v = spm * (numpy.exp(years*r)-1) / (numpy.exp(r/12)-1)
savings = spm*12*years
interests = total - savings
ratio = interests / savings
print(f"Savings                 : {savings:13.2f} $")
print(f"Interests (prediction)  : {v:13.2f} $")
print(f"Interests (actual)      : {interests:13.2f} $")
print(f"Interests (actual)      : {ratio*100:13.1f} %")

f = lambda y, r: spm*(numpy.exp(y*r)-1) / (numpy.exp(r/12)-1)
y = numpy.arange(1, years+1)
plt.plot(y, init + y * spm * 12, "--", label="R=0%")
plt.plot(y, init+f(y, 0.03), label="R=3%")
plt.plot(y, init+f(y, 0.05), label="R=5%")
plt.plot(y, init+f(y, 0.07), label="R=7%")
plt.plot(y, init+f(y, 0.10), label="R=10%")
#plt.axhline(1e6, 0, 1, linestyle="--", color="red")
plt.xlabel("Time [years]")
plt.ylabel("Savings [$]")
plt.legend()
plt.grid(True)
plt.show()
