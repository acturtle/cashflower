import datetime
import importlib
import inspect
import os
import pandas as pd

# from .modelvariable import ModelVariable

T_MAX = 1440


class ModelVariable:
    def __init__(self, function):
        self.function = function
        self.name = function.__name__
        self.result = [None] * T_MAX

    def __call__(self, t):
        if not self.result[t]:
            self.result[t] = self.function(t)
        return self.result[t]


project = "example"
model = "wol"
filepath = os.path.join(project, model, "model", "policy.py")
exec(open(filepath).read())

module_name = f"{project}.{model}.model.policy"
module = importlib.import_module(module_name)
module_functions = inspect.getmembers(module, inspect.isfunction)
module_functions = [func for func in module_functions if inspect.getmodule(func[1]) == module]

model_functions = []
for name, func in module_functions:
    exec(f"{name} = ModelVariable({name})")
    exec(f"model_functions.append({name})")


output = pd.DataFrame()
for model_function in model_functions:
    output[model_function.name] = [model_function(t) for t in range(T_MAX)]

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{timestamp}.csv"
output.to_csv(filename)
