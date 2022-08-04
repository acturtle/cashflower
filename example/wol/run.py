import datetime
import importlib
import inspect
import os

from cashflower.model import Model, ModelPoint, ModelVariable
from cashflower.utils import get_second_element
from example.wol.modelpoint import policy

# List model points
modelpoint_module = importlib.import_module("example.wol.modelpoint")
model_points = inspect.getmembers(modelpoint_module)
model_points = [model_point for model_point in model_points if isinstance(model_point[1], ModelPoint)]

# List model variables
policy_module = importlib.import_module("policy")
policy_model_variables = inspect.getmembers(policy_module)
policy_model_variables = [v for v in policy_model_variables if isinstance(v[1], ModelVariable)]
for name, obj in policy_model_variables:
    obj.name = name
    obj.submodel = "policy"
    obj.modelpoint = get_second_element(model_points, "policy")
    obj.modelpoint.name = "policy"

coverage_module = importlib.import_module("coverage")
coverage_model_variables = inspect.getmembers(coverage_module)
coverage_model_variables = [v for v in coverage_model_variables if isinstance(v[1], ModelVariable)]
for name, obj in coverage_model_variables:
    obj.name = name
    obj.submodel = "coverage"
    obj.modelpoint = get_second_element(model_points, "coverage")
    print("run ", obj.modelpoint)
    obj.modelpoint.name = "coverage"

# Create model
model = Model(variables=ModelVariable.instances)
model.set_children()
model.set_grandchildren()
model.set_queue()
model.calculate()


# print(model.output)

# Save results
# timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# filename = f"{timestamp}.csv"
# model.output.to_csv(filename)
