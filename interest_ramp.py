import matplotlib.pyplot as plt
import argparse
import datetime
import numpy

parser = argparse.ArgumentParser()
parser.add_argument("-y", "--years", type=int, default=5)
parser.add_argument("-i", "--initial", type=float, default=1000)
parser.add_argument("-r", "--interest-rate", type=float, default=4.5)
parser.add_argument("-s", "--savings-per-month", type=float, default=0)
args = parser.parse_args()

today = datetime.date.today()

def month_generator(starting_month):
    names = [
            "January", "February", "March", "April",
            "May", "June", "July", "August", "September",
            "October", "November", "December"]
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    current_month = starting_month
    while True:
        m = names[current_month]
        d = days[current_month]
        current_month = (current_month+1) % 12
        yield m, d

total = args.initial
monthly_total = []
r = args.interest_rate/100
month_gen = month_generator(today.month-1)
for year in range(today.year, today.year + args.years):
    print(f"Year {year}")
    for _ in range(12):
        month_name, days = next(month_gen)
        print(f"\t{month_name}")
        print(f"\t\tStart\t${total:.2f}")
        for iday in range(days):
            total *= 1+r/365
        total += args.savings_per_month
        monthly_total.append(total)
        print(f"\t\tEnd\t${total:.2f}")

interests = total - args.initial - 12*args.savings_per_month*args.years
print(f"Final     : ${total:.2f}")
print(f"Interests : +${interests:.2f}")

if args.initial != 0:
    growth = (total / args.initial - 1) * 100
    print(f"Growth    : +{growth:.1f}%")

x = range(args.years*12)
xticks = []
year = today.year
month_gen = month_generator(today.month-1)
for year in range(today.year, today.year + args.years):
    for _ in range(12):
        month_name, _ = next(month_gen)
        xticks.append(f"{month_name[:3]} {year%100}")
label = "R={:.2f}, SPM=${:.2f}".format(args.interest_rate, args.savings_per_month)
plt.plot(x, monthly_total, marker=".", label=label)
plt.legend()
plt.xticks(x, xticks, rotation=90)
plt.grid(True)
#plt.show()
