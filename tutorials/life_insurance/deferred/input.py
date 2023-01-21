import pandas as pd

from cashflower import Runplan, ModelPoint


runplan = Runplan(data=pd.DataFrame({"version": [1]}))


policy = ModelPoint(data=pd.DataFrame({
    "policy_id": [1],
    "sum_assured": [100_000],
    "deferral": [24],
}))


assumption = dict()
# assumption["mortality"] = pd.read_csv("")
