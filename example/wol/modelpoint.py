import pandas as pd

from cashflower.model import ModelPoint

policy = ModelPoint(pd.read_csv("C:/Users/admin/Desktop/model-input/policy_wol.csv"))
# policy = ModelPoint(pd.read_csv("C:/Users/admin/Desktop/model-input/wol_policy.csv"))
coverage = ModelPoint(pd.read_csv("C:/Users/admin/Desktop/model-input/wol_coverage.csv"))
