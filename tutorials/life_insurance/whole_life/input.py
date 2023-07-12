import pandas as pd

from cashflower import ModelPointSet


N = 1_000
main = ModelPointSet(data=pd.DataFrame({
    "id": [*range(N)],
    "sum_assured": [100_000 for _ in range(N)]
}))
