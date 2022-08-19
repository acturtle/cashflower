import pandas as pd

from cashflower import ModelPoint

data = pd.DataFrame({
    "value1": [1, 2, 3],
    "value2": ["a", "b", "c"]
})

policy = ModelPoint(data=data)
