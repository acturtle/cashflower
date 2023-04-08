from cashflower import assign, ModelVariable, Constant

from tutorials.asset.bond.input import main, runplan, assumption


t_end = Constant()
cal_month = ModelVariable(mp_dep=False)
cal_year = ModelVariable(mp_dep=False)
coupon = ModelVariable()
nominal_value = ModelVariable()
present_value = ModelVariable()


@assign(t_end)
def t_end_formula():
    years = main.get("term") // 12
    months = main.get("term") - years * 12

    end_year = main.get("issue_year") + years
    end_month = main.get("issue_month") + months

    if end_month > 12:
        end_year += 1
        end_month -= 12

    valuation_year = runplan.get("valuation_year")
    valuation_month = runplan.get("valuation_month")
    return (end_year - valuation_year) * 12 + (end_month - valuation_month)


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


@assign(coupon)
def coupon_formula(t):
    if t != 0 and t <= t_end() and cal_month(t) == main.get("issue_month"):
        return main.get("nominal") * main.get("coupon_rate")
    else:
        return 0


@assign(nominal_value)
def nominal_value_formula(t):
    if t == t_end():
        return main.get("nominal")
    else:
        return 0


@assign(present_value)
def present_value_formula(t):
    i = assumption["INTEREST_RATE"]
    return coupon(t) + nominal_value(t) + present_value(t+1) * (1/(1+i))**(1/12)
