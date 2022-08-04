from cashflower.model import ModelVariable

from example.wol.assumption import assumption
from example.wol.modelpoint import coverage
from example.wol.policy import mortality_rate, survival_rate


expected_benefit = ModelVariable()


def expected_benefit_formula(t):
    sum_assured = float(coverage.get("SUM_ASSURED"))
    _type = coverage.get("TYPE")

    if _type == "DEATH":
        return survival_rate(t - 1) * mortality_rate(t) * sum_assured
    elif _type == "ILLNESS":
        pass
    else:
        raise ValueError(f"Unknown coverage type {_type}.")


expected_benefit.formula = expected_benefit_formula
