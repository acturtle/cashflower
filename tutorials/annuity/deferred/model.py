from cashflower import variable

from tutorials.annuity.deferred.input import main
from tutorials.annuity.deferred.settings import settings


INTEREST_RATE = 0.005
DEATH_PROB = 0.003


@variable()
def survival_rate(t):
    if t == 0:
        return 1
    elif t == 1:
        return 1 - DEATH_PROB
    else:
        return survival_rate(t-1) * (1 - DEATH_PROB)


@variable()
def expected_payment(t):
    if t <= main.get("deferral"):
        return 0
    else:
        payment = main.get("payment")
        return survival_rate(t) * payment


@variable()
def actuarial_present_value(t):
    if t == settings["T_MAX_CALCULATION"]:
        return expected_payment(t)
    return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)
