from cashflower import variable

from tutorials.annuity.temporary.input import main

INTEREST_RATE = 0.005
DEATH_PROB = 0.003


@variable()
def survival_rate(t):
    if t == 0:
        return 1
    elif t == 1:
        return 1 - DEATH_PROB
    else:
        return survival_rate(t-1) * (1 - DEATH_PROB)


@variable()
def expected_payment(t):
    # if t == 0:
    #     return 0
    # elif t > main.get("remaining_term"):
    #     return 0
    # else:
    #     payment = main.get("payment")
    #     return survival_rate(t) * payment

    # How AST is seeing it:
    if t == 0:
        return 0
    else:
        if t > main.get("remaining_term"):
            return 0
        else:
            payment = main.get("payment")
            return survival_rate(t) * payment


@variable()
def actuarial_present_value(t):
    return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)
