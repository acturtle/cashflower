import os
import pandas as pd

filepath = os.path.join(os.path.dirname(__file__), "illustrative_life_table.csv")
illustrative_life_table = pd.read_csv(filepath, index_col="age")
