import pandas as pd
from cashflower import Runplan, ModelPointSet

STOCH = 2

runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({
    "id": [1],
    "premium": [1_000],
}))

assumption = {
    "indexation": 0.01,
    "discount_rates": pd.read_csv("./assumption/discount_rates_stoch.csv", index_col="t")
}
