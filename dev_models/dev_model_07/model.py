from cashflower import variable


@variable()
def a():
    return 1


@variable()
def b():
    return 2


@variable()
def c(t):
    return a() * t + b() + d(t)


@variable()
def d(t):
    if t == 0:
        return 0
    return c(t-1)


@variable()
def e(t):
    return d(t)


@variable()
def f(t):
    return e(t)


@variable()
def g(t):
    return e(t)


@variable()
def h(t):
    return g(t)
