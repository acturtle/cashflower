from cashflower import ModelPointSet
import pandas as pd

policy = ModelPointSet(data=pd.DataFrame({
    "id": range(1, 11),
    "premium": range(1, 11)
}))
