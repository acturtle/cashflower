import inspect
import importlib
import os
import pandas as pd


def calculate(project, model):
    output = {}
    module_filenames = [filename for filename in os.listdir(f'{project}/{model}/model') if filename.endswith('.py')]
    modules = [filename[:-3] for filename in module_filenames]

    for module in modules:
        imported_module = importlib.import_module(f'{project}.{model}.model.{module}')
        members = inspect.getmembers(imported_module, inspect.isfunction)
        members = [member for member in members if inspect.getmodule(member[1]) == imported_module]

        module_output = pd.DataFrame()
        for func_name, func in members:
            if "t" in inspect.signature(func).parameters:
                module_output[func_name] = [func(t) for t in range(100)]
            else:
                module_output[func_name] = [func() for t in range(100)]

        output[module] = module_output

    return output
