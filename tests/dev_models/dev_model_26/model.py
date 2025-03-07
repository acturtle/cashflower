from cashflower import variable
from input import policy


@variable()
def premium_cf(t):
    return policy.get("premium")
