from cashflower import assign, ModelVariable

from tutorials.whole_life.input import policy, assumption


age = ModelVariable()
death_prob = ModelVariable()
survival_rate = ModelVariable()
expected_premium = ModelVariable()
expected_benefit = ModelVariable()
projection_year = ModelVariable(pol_dep=False)
yearly_spot_rate = ModelVariable(pol_dep=False)
yearly_forward_rate = ModelVariable(pol_dep=False)
forward_rate = ModelVariable(pol_dep=False)
discount_rate = ModelVariable(pol_dep=False)
pv_expected_premium = ModelVariable()
pv_expected_benefit = ModelVariable()
best_estimate_liabilities = ModelVariable()


@assign(age)
def age_formula(t):
    if t == 0:
        return int(policy.get("age"))
    elif t % 12 == 0:
        return age(t-1) + 1
    else:
        return age(t-1)


@assign(death_prob)
def death_prob_formula(t):
    sex = policy.get("sex")
    if age(t) == age(t-1):
        return death_prob(t-1)
    elif age(t) <= 100:
        yearly_rate = assumption["mortality"].loc[age(t)][sex]
        monthly_rate = (1 - (1 - yearly_rate)**(1/12))
        return round(monthly_rate, 6)
    else:
        return 1


@assign(survival_rate)
def survival_rate_formula(t):
    if t == 0:
        return 1 - death_prob(t)
    else:
        return round(survival_rate(t-1) * (1 - death_prob(t)), 6)


@assign(expected_premium)
def expected_premium_formula(t):
    premium = policy.get("premium")
    return round(premium * survival_rate(t-1), 2)


@assign(expected_benefit)
def expected_benefit_formula(t):
    sum_assured = policy.get("sum_assured")
    return round(survival_rate(t-1) * death_prob(t) * sum_assured, 2)


@assign(projection_year)
def projection_year_formula(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year(t - 1) + 1
    else:
        return projection_year(t - 1)


@assign(yearly_spot_rate)
def yearly_spot_rate_formula(t):
    if t == 0:
        return 0
    else:
        return round(assumption["interest_rates"].loc[projection_year(t)]["value"], 6)


@assign(yearly_forward_rate)
def yearly_forward_rate_formula(t):
    if t == 0:
        return 0
    elif t == 1:
        return yearly_spot_rate(t)
    elif t % 12 != 1:
        return yearly_forward_rate(t-1)
    else:
        return round(((1+yearly_spot_rate(t))**projection_year(t))/((1+yearly_spot_rate(t-1))**projection_year(t-1)) - 1, 6)


@assign(forward_rate)
def forward_rate_formula(t):
    return round((1+yearly_forward_rate(t))**(1/12)-1, 6)


@assign(discount_rate)
def discount_rate_formula(t):
    return round(1/(1+forward_rate(t)), 6)


@assign(pv_expected_premium)
def pv_expected_premium_formula(t):
    return round(expected_premium(t) + pv_expected_premium(t+1) * discount_rate(t+1), 2)


@assign(pv_expected_benefit)
def pv_expected_benefit_formula(t):
    return round(expected_benefit(t) + pv_expected_benefit(t+1) * discount_rate(t+1), 2)


@assign(best_estimate_liabilities)
def best_estimate_liabilities_formula(t):
    return round(pv_expected_benefit(t) - pv_expected_premium(t), 2)
