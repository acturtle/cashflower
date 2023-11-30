from cashflower import variable


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
