from cashflower.model import ModelVariable
from cashflower.utils import get_cell

from example.wol.modelpoint import policy
from example.wol.assumption import assumption

age = ModelVariable()
mortality_rate = ModelVariable()
survival_rate = ModelVariable()
# expected_premium = ModelVariable()
# expected_benefit = ModelVariable()
# projection_year = ModelVariable()
# yearly_spot_rate = ModelVariable()
# yearly_forward_rate = ModelVariable()
# forward_rate = ModelVariable()
# discount_rate = ModelVariable()
# pv_expected_premium = ModelVariable()
# pv_expected_benefit = ModelVariable()
# best_estimate_liabilities = ModelVariable()


def age_formula(t):
    if t == 0:
        return int(policy.get("AGE"))
    elif t % 12 == 0:
        return age(t-1) + 1
    else:
        return age(t-1)


def mortality_rate_formula(t):
    sex = policy.get("SEX")
    if age(t) <= 100:
        yearly_rate = float(get_cell(assumption["mortality"], sex, AGE=age(t)))
        monthly_rate = (1 - (1 - yearly_rate)**(1/12))
        return monthly_rate
    else:
        return 1


def morbidity_rate_formula(t):
    sex = policy.get("SEX")
    if age(t) <= 100:
        yearly_rate = float(get_cell(assumption["morbidity"], sex, AGE=age(t)))
        monthly_rate = (1 - (1 - yearly_rate)**(1/12))
        return monthly_rate
    else:
        return 1


def survival_rate_formula(t):
    if t == 0:
        return 1 - mortality_rate(t)
    else:
        return survival_rate(t-1) * (1 - mortality_rate(t))


def expected_premium_formula(t):
    premium = float(policy.get("PREMIUM"))
    return premium * survival_rate(t-1)

#
# def expected_benefit_formula(t):
#     sum_assured = float(policy.get("SUM_ASSURED"))
#     return survival_rate(t-1) * mortality_rate(t) * sum_assured
#
#
# def projection_year_formula(t):
#     if t == 0:
#         return 0
#     elif t == 1:
#         return 1
#     elif t % 12 == 1:
#         return projection_year(t - 1) + 1
#     else:
#         return projection_year(t - 1)
#
#
# def yearly_spot_rate_formula(t):
#     if t == 0:
#         return 0
#     else:
#         return get_cell(assumption["interest_rates"], "VALUE", T=projection_year(t))
#
#
# def yearly_forward_rate_formula(t):
#     if t == 0:
#         return 0
#     elif t == 1:
#         return yearly_spot_rate(t)
#     elif t % 12 != 1:
#         return yearly_forward_rate(t-1)
#     else:
#         return ((1+yearly_spot_rate(t))**projection_year(t))/((1+yearly_spot_rate(t-1))**projection_year(t-1)) - 1
#
#
# def forward_rate_formula(t):
#     return (1+yearly_forward_rate(t))**(1/12)-1
#
#
# def discount_rate_formula(t):
#     return 1/(1+forward_rate(t))
#
#
# def pv_expected_premium_formula(t):
#     return expected_premium(t) + pv_expected_premium(t+1) * discount_rate(t)
#
#
# def pv_expected_benefit_formula(t):
#     return expected_benefit(t) + pv_expected_benefit(t+1) * discount_rate(t)
#
#
# def best_estimate_liabilities_formula(t):
#     return pv_expected_benefit(t) - pv_expected_premium(t)


age.formula = age_formula
mortality_rate.formula = mortality_rate_formula
survival_rate.formula = survival_rate_formula
# expected_premium.formula = expected_premium_formula
# expected_benefit.formula = expected_benefit_formula
# projection_year.formula = projection_year_formula
# yearly_spot_rate.formula = yearly_spot_rate_formula
# yearly_forward_rate.formula = yearly_forward_rate_formula
# forward_rate.formula = forward_rate_formula
# discount_rate.formula = discount_rate_formula
# pv_expected_premium.formula = pv_expected_premium_formula
# pv_expected_benefit.formula = pv_expected_benefit_formula
# best_estimate_liabilities.formula = best_estimate_liabilities_formula
