import pandas as pd

from cashflower import ModelPoint


policy = ModelPoint(data=pd.DataFrame({
    "policy_id": [1],
    "sum_assured": [100_000],
    "deferral": [24],
}))
