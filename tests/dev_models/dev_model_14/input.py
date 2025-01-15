import pandas as pd
from cashflower import CSVReader, Runplan, ModelPointSet


runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({"id": [1]}))

assumption = {
    "discount_rate": CSVReader("data/discount_rate.csv"),
    "payment": CSVReader("data/payment.csv")
}
