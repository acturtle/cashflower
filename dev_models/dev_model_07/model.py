from cashflower import variable


@variable()
def a(t):
    return 1 * t


@variable()
def b(t):
    return 2 * t


@variable()
def c(t):
    return 3 * t
