import pandas as pd
from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6, 7, 8],
    "group": ["A", "B", "C", "A", "B", "A", "C", "A"]
}))

assumption = dict()
