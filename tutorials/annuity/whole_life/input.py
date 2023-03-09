import pandas as pd

from cashflower import Runplan, ModelPointSet


policy = ModelPointSet(data=pd.DataFrame({
    "id": [1],
    "payment": [1_000]
}))
