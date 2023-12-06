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
def discount_rate1(t):
    if t == 0:
        return 1
    return assumption["discount_rates"].loc[t]["value1"]


@variable()
def discount_rate2(t):
    if t == 0:
        return 1
    return assumption["discount_rates"].loc[t]["value2"]


@variable()
def pv_premiums1(t):
    if t == settings["T_MAX_CALCULATION"]:
        return premium(t)
    return premium(t) + pv_premiums1(t+1) * discount_rate1(t+1)


@variable()
def pv_premiums2(t):
    if t == settings["T_MAX_CALCULATION"]:
        return premium(t)
    return premium(t) + pv_premiums2(t+1) * discount_rate2(t+1)


@variable(array=True)
def pv_premiums_avg():
    return (pv_premiums1() + pv_premiums2())/2
