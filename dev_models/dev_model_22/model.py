from cashflower import variable


@variable()
def a(t):
    if t == 0:
        return 0
    else:
        return b(t - 1)


@variable()
def b(t):
    return a(t) - y(t) - x(t)


@variable()
def x(t):
    return a(t)


@variable()
def y(t):
    return a(t)


@variable()
def c(t):
    return b(t) + e(t)


@variable()
def d(t):
    return c(t)


@variable()
def e(t):
    if t == 0:
        return 0
    else:
        return d(t-1)

