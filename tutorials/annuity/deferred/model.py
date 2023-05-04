from cashflower import assign, ModelVariable

from tutorials.annuity.deferred.input import main


INTEREST_RATE = 0.005
DEATH_PROB = 0.003

survival_rate = ModelVariable()
expected_payment = ModelVariable()
actuarial_present_value = ModelVariable()


@assign(survival_rate)
def _survival_rate(t):
    if t == 0:
        return 1
    elif t == 1:
        return 1 - DEATH_PROB
    else:
        return survival_rate(t-1) * (1 - DEATH_PROB)


@assign(expected_payment)
def _expected_payment(t):
    if t <= main.get("deferral"):
        return 0
    else:
        payment = main.get("payment")
        return survival_rate(t) * payment


@assign(actuarial_present_value)
def _actuarial_present_value(t):
    return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)
