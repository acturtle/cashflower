from cashflower import cython, variable
from input import assumption
from settings import settings


@variable()
def payment(t):
    return int(assumption["payment"].get_value(str(t), "value"))


@variable()
def discount_rate(t):
    return float(assumption["discount_rate"].get_value(str(t), "value"))


@variable()
def present_value1(t):
    if t == settings["T_MAX_CALCULATION"]:
        return payment(t)
    else:
        return payment(t) + present_value1(t+1) * discount_rate(t+1)


@variable(array=True)
def present_value2():
    return cython(cash_flows=payment(), discount_rates=discount_rate())
