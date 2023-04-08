import pandas as pd

from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({
    "version": [1],
    "valuation_year": [2022],
    "valuation_month": [12],
}))


main = ModelPointSet(data=pd.DataFrame({
    "id": [1],
    "nominal": [1000],
    "coupon_rate": [0.03],
    "term": [120],
    "issue_year": [2022],
    "issue_month": [6],
}))


assumption = dict()
assumption["INTEREST_RATE"] = 0.02
