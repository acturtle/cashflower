import math
from cashflower import assign, ModelVariable, Constant

from tutorials.time.input import main, runplan

cal_month = ModelVariable(model_point_set=main, mp_dep=False)
cal_year = ModelVariable(model_point_set=main, mp_dep=False)
elapsed_months = Constant(model_point_set=main)
pol_month = ModelVariable(model_point_set=main)
pol_year = ModelVariable(model_point_set=main)


@assign(cal_month)
def cal_month_formula(t):
    if t == 0:
        return runplan.get("valuation_month")
    if cal_month(t-1) == 12:
        return 1
    else:
        return cal_month(t-1) + 1


@assign(cal_year)
def cal_year_formula(t):
    if t == 0:
        return runplan.get("valuation_year")
    if cal_month(t-1) == 12:
        return cal_year(t-1) + 1
    else:
        return cal_year(t-1)


@assign(elapsed_months)
def elapsed_months_formula():
    issue_year = main.get("issue_year")
    issue_month = main.get("issue_month")
    valuation_year = runplan.get("valuation_year")
    valuation_month = runplan.get("valuation_month")
    return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


@assign(pol_month)
def pol_month_formula(t):
    if t == 0:
        mnth = elapsed_months() % 12
        mnth = 12 if mnth == 0 else mnth
        return mnth
    if pol_month(t-1) == 12:
        return 1
    return pol_month(t-1) + 1


@assign(pol_year)
def pol_year_formula(t):
    if t == 0:
        return math.floor(elapsed_months() / 12)
    if pol_month(t) == 1:
        return pol_year(t-1) + 1
    return pol_year(t-1)
