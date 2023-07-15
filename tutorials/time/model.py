import math
from cashflower import variable

from input import main, runplan


@variable(repeat=True)
def cal_month(t):
    if t == 0:
        return runplan.get("valuation_month")
    if cal_month(t-1) == 12:
        return 1
    else:
        return cal_month(t-1) + 1


@variable(repeat=True)
def cal_year(t):
    if t == 0:
        return runplan.get("valuation_year")
    if cal_month(t-1) == 12:
        return cal_year(t-1) + 1
    else:
        return cal_year(t-1)


@variable()
def elapsed_months():
    issue_year = main.get("issue_year")
    issue_month = main.get("issue_month")
    valuation_year = runplan.get("valuation_year")
    valuation_month = runplan.get("valuation_month")
    return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


@variable()
def pol_month(t):
    if t == 0:
        mnth = elapsed_months() % 12
        mnth = 12 if mnth == 0 else mnth
        return mnth
    if pol_month(t-1) == 12:
        return 1
    return pol_month(t-1) + 1


@variable()
def pol_year(t):
    if t == 0:
        return math.floor(elapsed_months(t) / 12)
    if pol_month(t) == 1:
        return pol_year(t-1) + 1
    return pol_year(t-1)
