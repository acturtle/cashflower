import pandas as pd
from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({
    "id": [1, 2, 3]
}))

fund = ModelPointSet(data=pd.DataFrame({
    "id": [1, 1, 2, 3, 3],
    "fund_value": [100, 200, 300, 400, 500]
}))
