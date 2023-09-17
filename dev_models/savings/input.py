import pandas as pd
from cashflower import Runplan, ModelPointSet, CSVReader


runplan = Runplan(data=pd.DataFrame({
    "version": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "scen_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}))

# model_point_table = pd.read_csv("input/model_point_samples.csv")
model_point_table = pd.read_csv("input/model_point_table_100K.csv")
product_spec_table = pd.read_csv("input/product_spec_table.csv")
main_data = model_point_table.merge(product_spec_table, on="spec_id", how="left")
main = ModelPointSet(data=main_data)

assumption = {
    "disc_rate_ann": CSVReader("input/disc_rate_ann.csv"),
    "mort_table": CSVReader("input/mort_table.csv"),
    "surr_charge_table": CSVReader("input/surr_charge_table.csv"),
    "std_norm_rand": CSVReader("input/std_norm_rand.csv", num_row_label_cols=2),
    "expense_acq": 5000,
    "expense_maint": 500,
    "inflation_rate": 0.01,
}
