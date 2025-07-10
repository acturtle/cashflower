from cashflower import variable


@variable()
def a(t):
    return t * 2


@variable()
def b(t):
    return t + 5
