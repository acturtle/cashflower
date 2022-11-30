import pandas as pd

from cashflower import Runplan, ModelPoint


runplan = Runplan(data=pd.DataFrame({"version": [1]}))


policy = ModelPoint(data=pd.DataFrame({
    "policy_id": ["a", "b"],
    "age": [32, 40],
    "sex": ["male", "female"],
    "sum_assured": [100_000, 80_000],
    "premium": [140, 110]
}))

assumption = dict()
assumption["mortality"] = pd.read_csv("./input/mortality.csv")
assumption["interest_rates"] = pd.read_csv("./input/interest_rates.csv")

