import pandas as pd
from cashflower import ModelPointSet

my_data = pd.read_csv("data.csv")

policy = ModelPointSet(data=pd.DataFrame({
    "id": range(10_000)
}))
