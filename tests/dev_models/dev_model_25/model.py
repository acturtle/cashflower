from cashflower import variable
from input import fund


@variable()
def total_fund_value():
    total_value = 0
    for i in range(0, fund.model_point_data.shape[0]):
        total_value += fund.get("fund_value", i)
    return total_value
