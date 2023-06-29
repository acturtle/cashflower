from cashflower import variable

from tutorials.asset.bond.input import main, runplan, assumption


@variable()
def t_end(t):
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


@variable()
def cal_month(t):
    if t == 0:
        return runplan.get("valuation_month")
    if cal_month(t-1) == 12:
        return 1
    else:
        return cal_month(t-1) + 1


@variable()
def cal_year(t):
    if t == 0:
        return runplan.get("valuation_year")
    if cal_month(t-1) == 12:
        return cal_year(t-1) + 1
    else:
        return cal_year(t-1)


@variable()
def coupon(t):
    if t != 0 and t <= t_end(t) and cal_month(t) == main.get("issue_month"):
        return main.get("nominal") * main.get("coupon_rate")
    else:
        return 0


@variable()
def nominal_value(t):
    if t == t_end(t):
        return main.get("nominal")
    else:
        return 0


@variable()
def present_value(t):
    i = assumption["INTEREST_RATE"]
    return coupon(t) + nominal_value(t) + present_value(t+1) * (1/(1+i))**(1/12)
