import pandas as pd
from cashflower import Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({"id": [1]}))

assumption = dict()
