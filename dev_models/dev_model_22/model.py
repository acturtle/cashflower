from cashflower import variable


@variable()
def a(t):
    return b(t-1)


@variable()
def b(t):
    if t == 0:
        return 1
    else:
        return a(t)
