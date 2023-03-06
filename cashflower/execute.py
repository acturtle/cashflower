from cashflower import *

def execute(part, cpu_count, settings):
    model_name = "example"
    settings = load_settings(settings)
    input_module = importlib.import_module(model_name + ".input")
    model_module = importlib.import_module(model_name + ".model")

    # input.py contains runplan and modelpoints
    input_members = inspect.getmembers(input_module)
    runplan = get_runplan(input_members)
    modelpoints, policy = get_modelpoints(input_members, settings)

    # model.py contains model variables and constants
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, policy, settings)
    constants = get_constants(model_members, policy)

    # Run model on multiple cpus
    model = Model(model_name, variables, constants, modelpoints, settings, cpu_count)
    output = model.run(part)
    return output