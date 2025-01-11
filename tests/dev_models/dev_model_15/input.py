import pandas as pd
from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "product_code": ["C", "B", "B", "A", "A", "B", "B", "A", "A", "C", "C", "C"]
}))

assumption = dict()
