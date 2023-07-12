from cashflower import variable

from tutorials.life_insurance.deferred.input import main
from tutorials.life_insurance.deferred.settings import settings

INTEREST_RATE = 0.005
DEATH_PROB = 0.003


@variable()
def survival_rate(t):
    if t == 0:
        return 1 - DEATH_PROB
    return survival_rate(t-1) * (1 - DEATH_PROB)


@variable()
def expected_benefit(t):
    if t < main.get("deferral"):
        return 0
    return survival_rate(t-1) * DEATH_PROB * main.get("sum_assured")


@variable()
def net_single_premium(t):
    if t == settings["T_MAX_CALCULATION"]:
        return expected_benefit(t)
    return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)
