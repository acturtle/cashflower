from cashflower import variable

from tutorials.annuity.temporary.input import main
from tutorials.annuity.temporary.settings import settings

INTEREST_RATE = 0.005
DEATH_PROB = 0.003


@variable()
def survival_rate(t):
    if t == 0:
        return 1
    return survival_rate(t-1) * (1 - DEATH_PROB)


@variable()
def expected_payment(t):
    if t == 0 or t > main.get("remaining_term"):
        return 0
    return survival_rate(t) * main.get("payment")


@variable()
def actuarial_present_value(t):
    if t == settings["T_MAX_CALCULATION"]:
        return expected_payment(t)
    return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)
