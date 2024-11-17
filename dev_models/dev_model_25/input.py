import pandas as pd
from cashflower import Runplan, ModelPointSet

runplan = Runplan(data=pd.DataFrame({"version": [1]}))

policy = ModelPointSet(data=pd.DataFrame({
    "id": [1, 2, 3]
}), id_column="id")

fund = ModelPointSet(data=pd.DataFrame({
    "id": [1, 1, 3, 3],
    "fund_value": [100, 200, 400, 500]
}),
    main=False, id_column="id")
