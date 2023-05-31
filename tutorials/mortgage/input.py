import pandas as pd

from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))


main = ModelPointSet(data=pd.DataFrame({
    "id": [1],
    "loan": [100_000],
    "interest_rate": [0.1],
    "term": [360]
}))


assumption = dict()
# assumption["mortality"] = pd.read_csv("")
