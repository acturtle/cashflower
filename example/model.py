from cashflower import variable


# Real estate mortgage
@variable()
def interest(t):
    if t == 0:
        return 0
    return balance(t-1) * 0.001


@variable()
def principal(t):
    if t == 0:
        return 0
    return 1_000 - interest(t)


@variable()
def balance(t):
    if t == 0:
        return 50_000
    else:
        return balance(t-1) - principal(t)


# My independent variable
@variable()
def my_independent_variable(t):
    return 2*t


# Another cycle [a, b, c]
@variable()
def a(t):
    return b(t)


@variable()
def b(t):
    return c(t)


@variable()
def c(t):
    if t == 0:
        return 2
    else:
        return a(t-1)


# Yet another cycle [x, y, z]
@variable()
def x(t):
    if t < 6:
        return t
    if t > 6:
        return 12
    if t == 6:
        return y(t)


@variable()
def y(t):
    if t == 6:
        return 6
    return z(t)


@variable()
def z(t):
    if t == 0:
        return 424242

    if t == 12:
        return 121212

    if t < 6:
        return x(t-1)

    # if t > 6:
    #     return x(t+1)

    return 999
