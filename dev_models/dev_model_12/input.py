import pandas as pd
from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({
    "version": [1, 2, 3],
    "shock": [1, 1.5, 0.5],
}))

main = ModelPointSet(data=pd.DataFrame({"id": [1]}))

assumption = dict()
