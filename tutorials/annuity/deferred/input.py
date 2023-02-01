import pandas as pd

from cashflower import Runplan, ModelPoint


policy = ModelPoint(data=pd.DataFrame({
    "policy_id": [1],
    "payment": [1_000],
    "deferral": [12],
}))
