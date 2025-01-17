from cashflower import variable


@variable()
def my_var(t, stoch):
    return t * stoch
