from cashflower import variable
from input import main


@variable()
def monthly_interest_rate():
    return main.get("interest_rate") / 12


@variable()
def payment():
    L = main.get("loan")
    n = main.get("term")
    j = monthly_interest_rate()
    v = 1 / (1 + j)
    ann = (1 - v ** n) / j
    return L / ann


@variable()
def balance(t):
    if t == 0:
        return main.get("loan")
    else:
        return balance(t-1) - principal(t)


@variable()
def principal(t):
    if t == 0:
        return 0
    return payment(t) - interest(t)


@variable()
def interest(t):
    if t == 0:
        return 0
    return balance(t-1) * monthly_interest_rate(t)
