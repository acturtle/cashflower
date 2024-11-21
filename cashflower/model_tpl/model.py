from cashflower import variable


# Define a variable for calculating survival probability at each time step.
@variable()
def survival_probability(t):
    """
    Calculate the probability of survival.
    - Assumes a constant mortality rate of 1% per time step.
    - At t=0, the probability is 1 (certain survival).
    - For t > 0, survival probability decreases iteratively.
    """
    mortality_rate = 0.01
    if t == 0:
        return 1
    return survival_probability(t - 1) * (1 - mortality_rate)
