from cashflower import assign, ModelVariable, Constant

from tutorials.mortgage.input import main


monthly_interest_rate = Constant(model_point_set=main)
payment = Constant(model_point_set=main)
balance = ModelVariable(model_point_set=main)
interest = ModelVariable(model_point_set=main)
principal = ModelVariable(model_point_set=main)


@assign(monthly_interest_rate)
def _monthly_interest_rate():
    return main.get("interest_rate") / 12


@assign(payment)
def _payment():
    L = main.get("loan")
    n = main.get("term")
    j = monthly_interest_rate()
    v = 1 / (1 + j)
    ann = (1 - v ** n) / j
    return L / ann


@assign(balance)
def _balance(t):
    if t == 0:
        return main.get("loan")
    else:
        return balance(t-1) - principal(t)


@assign(principal)
def _principal(t):
    if t == 0:
        return 0
    return payment() - interest(t)


@assign(interest)
def _interest(t):
    if t == 0:
        return 0
    return balance(t-1) * monthly_interest_rate()
