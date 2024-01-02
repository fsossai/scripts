import numpy

init = 0 # initial amount [$]
spm = 1000 # savings per month [$]
years = 1 # number of years to simulate

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

y = []
to = 100
for ir in range(1,to):
    r = ir/100
    print("\t",ir)
    total = init
    for iyear in range(years):
        print(f"Year {iyear+1}")
        for imonth, month_name in enumerate(months):
            print(f"\t{month_name}")
            print(f"\t\tStart\t${total:.10f}")
            for iday in range(days_in_month[imonth]):
                total *= 1+r/365
            total += spm
            print(f"\t\tEnd\t${total:.10f}")
    print(f"Final: ${total:.20f}")
    #y.append((total/(spm*12)-1)/(numpy.exp(r)-1))
    y.append((total/(spm*12)-1)/r)


import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy

poly1 = lambda x, m, q: m*x+q
x = numpy.arange(1, 100) / 100
y = numpy.array(y)
#y *= 100
param1, _ = curve_fit(poly1, x, y)
#param1 = [-1/12,46]

plt.plot(x, 1+x*y)
plt.plot(x, 1+x*poly1(x, *param1), "--")
mf = (1 + x/365)**30
plt.plot(x, (mf**12-1)/(mf-1)/12)
plt.show()

