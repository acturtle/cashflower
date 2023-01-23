from cashflower import assign, ModelVariable

from tutorials.life_insurance.term_life.input import policy

INTEREST_RATE = 0.005
DEATH_PROB = 0.003

survival_rate = ModelVariable()
expected_benefit = ModelVariable()
net_single_premium = ModelVariable()


@assign(survival_rate)
def survival_rate_formula(t):
    if t == 0:
        return 1 - DEATH_PROB
    else:
        return survival_rate(t-1) * (1 - DEATH_PROB)


@assign(expected_benefit)
def expected_benefit_formula(t):
    if t > policy.get("remaining_term"):
        return 0
    return survival_rate(t-1) * DEATH_PROB * policy.get("sum_assured")


@assign(net_single_premium)
def net_single_premium_formula(t):
    return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)
