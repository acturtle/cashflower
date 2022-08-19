from cashflower import assign, ModelVariable


projection_year = ModelVariable()


@assign(projection_year)
def projection_year_formula(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year(t - 1) + 1
    else:
        return projection_year(t - 1)
