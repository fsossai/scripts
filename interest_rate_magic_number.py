import numpy
import scipy.optimize
import matplotlib.pyplot as plt

for l, r in [(2,4), (4,6), (6,8), (8,10)]:
    irates = numpy.arange(l, r, 0.1)
    get_years = lambda irate, goal: numpy.log(goal) / numpy.log(1+irate/100)
    apx_years = lambda irate, magic_number: magic_number / irate

    goals = numpy.linspace(1, 2, 10)
    magic_numbers = []
    for goal in goals:
        years = get_years(irates, goal)
        popt, _ = scipy.optimize.curve_fit(apx_years, irates, years)
        magic_numbers.append(popt)

    plt.plot(goals, magic_numbers, label=f"[{l},{r}]")
plt.grid(True)
plt.legend()
plt.show()

