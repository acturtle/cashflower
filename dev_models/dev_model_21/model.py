from cashflower import variable
from input import main


@variable()
def monthly_interest_rate():
    return 0.001


@variable()
def payment():
    return 1_000


@variable()
def interest(t, stoch):
    if t == 0:
        return 0
    return balance(t-1, stoch) * monthly_interest_rate() * stoch


@variable()
def principal(t, stoch):
    if t == 0:
        return 0
    return payment() - interest(t, stoch)


@variable()
def balance(t, stoch):
    if t == 0:
        return 200_000
    else:
        return balance(t-1, stoch) - principal(t, stoch)
