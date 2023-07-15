import pandas as pd
from cashflower import ModelPointSet


main = ModelPointSet(data=pd.DataFrame({
    "id": [1],
    "sum_assured": [100_000],
    "remaining_term": [36],
}))
