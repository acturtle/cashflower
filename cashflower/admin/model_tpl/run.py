import datetime
import importlib
import inspect

from cashflower.model import Model, ModelVariable
from example.wol.input.modelpoint import policy

# Settings
settings = {}
module = importlib.import_module("settings")
module_variables = inspect.getmembers(module)
for variable in module_variables:
    if not variable[0].startswith("__"):
        settings[variable[0]] = variable[1]


# User defines model functions
exec(open("model/policy.py").read())
module_name = "model.policy"
module = importlib.import_module(module_name)
module_functions = inspect.getmembers(module, inspect.isfunction)
module_functions = [func for func in module_functions if inspect.getmodule(func[1]) == module]

# Functions are turned into model variables
model_variables = []
for name, func in module_functions:
    exec(f"{name} = ModelVariable({name}, settings=settings)")
    exec(f"model_variables.append({name})")

# Model encompasses model point and model variables
model = Model(model_point=policy, model_variables=model_variables)
model.calculate()
output = model.output

# Results are saved to file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{timestamp}.csv"
output.to_csv(filename)
