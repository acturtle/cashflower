from cashflower import variable
from input import assumption, main, runplan


@variable()
def a(t):
    return b(t)


@variable()
def b(t):
    return c(t)

@variable()
def c(t):
    return a(t)
