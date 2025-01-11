from cashflower import variable
from input import assumption, main
from settings import settings


@variable()
def discounted_premium(t):
    if t == settings["T_MAX_CALCULATION"]:
        return main.get("premium")
    return main.get("premium") + discounted_premium(t+1) * assumption["v"]
