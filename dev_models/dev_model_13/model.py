from cashflower import variable


@variable()
def projection_year(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year(t - 1) + 1
    else:
        return projection_year(t - 1)


@variable(array=True)
def my_var():
    return projection_year() * 2
