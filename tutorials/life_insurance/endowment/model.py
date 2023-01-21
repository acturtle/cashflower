from cashflower import assign, ModelVariable, Constant

from tutorials.life_insurance.pure_endowment.input import policy

YEARLY_INTEREST_RATE = 0.05
YEARLY_MORTALITY_RATE = 0.03


death_prob = ModelVariable()
survival_rate = ModelVariable()
discount_rate = Constant()
expected_benefit = ModelVariable()
net_single_premium = ModelVariable()


@assign(death_prob)
def death_prob_formula(t):
    if t == 1200:
        return 1
    return 1 - (1-YEARLY_MORTALITY_RATE)**(1/12)


@assign(discount_rate)
def discount_rate_formula():
    monthly_rate = (1+YEARLY_INTEREST_RATE)**(1/12) - 1
    return 1/(1+monthly_rate)


@assign(survival_rate)
def survival_rate_formula(t):
    if t == 0:
        return 1 - death_prob(t)
    else:
        return survival_rate(t-1) * (1 - death_prob(t))


@assign(expected_benefit)
def expected_benefit_formula(t):
    if t < policy.get("remaining_term"):
        return survival_rate(t-1) * death_prob(t) * policy.get("sum_assured")
    elif t == policy.get("remaining_term"):
        return survival_rate(t) * policy.get("sum_assured")
    else:
        return 0


@assign(net_single_premium)
def net_single_premium_formula(t):
    return expected_benefit(t) + net_single_premium(t+1) * discount_rate()
