from cashflower import variable
from input import assumption, main, runplan


@variable()
def premium():
    return 100 * runplan.get("shock")
