import pandas as pd
from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "group": ["A", "B", "A", "B", "C", "D", "A", "C", "D", "B", "A", "B"]
}))

assumption = dict()
