import pandas as pd

from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({
    "version": [1],
    "valuation_year": [2022],
    "valuation_month": [12]
}))


policy = ModelPointSet(data=pd.DataFrame({
    "id": [1],
    "issue_year": [2020],
    "issue_month": [6],
}))


assumption = dict()
# assumption["mortality"] = pd.read_csv("")
