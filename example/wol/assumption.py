import pandas as pd


assumption = dict()
assumption["mortality"] = pd.read_csv("C:/Users/admin/Desktop/model-input/mortality.csv")
assumption["morbidity"] = pd.read_csv("C:/Users/admin/Desktop/model-input/morbidity.csv")
assumption["interest_rates"] = pd.read_csv("C:/Users/admin/Desktop/model-input/interest_rates.csv")
