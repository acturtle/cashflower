from cashflower import variable


@variable(aggregation_type="first")
def projection_year_first(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year_first(t - 1) + 1
    else:
        return projection_year_first(t - 1)


@variable()
def projection_year_sum(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year_sum(t - 1) + 1
    else:
        return projection_year_sum(t - 1)
