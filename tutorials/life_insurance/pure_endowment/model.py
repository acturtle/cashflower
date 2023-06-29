from cashflower import variable

from tutorials.life_insurance.pure_endowment.input import main

INTEREST_RATE = 0.005
DEATH_PROB = 0.003


@variable()
def survival_rate(t):
    if t == 0:
        return 1 - DEATH_PROB
    else:
        return survival_rate(t-1) * (1 - DEATH_PROB)


@variable()
def expected_benefit(t):
    if t == main.get("remaining_term"):
        return survival_rate(t) * main.get("sum_assured")
    return 0


@variable()
def net_single_premium(t):
    return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)
