from cashflower import variable
from input import assumption, main
from settings import settings


@variable()
def premium(t):
    if t == 0:
        return main.get("premium")
    elif t % 12 == 0:
        return premium(t-1) * (1 + assumption["indexation"])
    else:
        return premium(t-1)


@variable()
def discount_rate(t):
    """Forward discount rates"""
    if t == 0:
        return 1
    return assumption["discount_rates"].loc[t]["value"]


@variable()
def pv_premiums(t):
    if t == settings["T_MAX_CALCULATION"]:
        return premium(t)
    return premium(t) + pv_premiums(t+1) * discount_rate(t+1)
