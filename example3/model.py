from cashflower import variable
from input import assumption, main, runplan


@variable()
def my_var(t):
    if t == 0:
        return 0

    if t == 12:
        return 12

    if t < 6:
        return my_var(t-1)

    if t > 6:
        return my_var(t+1)
