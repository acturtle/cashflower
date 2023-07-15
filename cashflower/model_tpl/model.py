from cashflower import variable
from input import assumption, main, runplan


@variable()
def projection_year(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year(t - 1) + 1
    else:
        return projection_year(t - 1)
