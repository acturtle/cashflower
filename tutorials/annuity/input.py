import pandas as pd

from cashflower import Runplan, ModelPoint


runplan = Runplan(data=pd.DataFrame({"version": [1]}))


policy = ModelPoint(data=pd.DataFrame({
    "policy_id": ["a", "b"],
    "age": [65, 30],
    "sex": ["female", "male"],
    "payment": [1750, 1000]
}))


assumption = dict()
assumption["mortality"] = pd.read_csv("./input/mortality.csv")
assumption["interest_rates"] = pd.read_csv("./input/interest_rates.csv")
