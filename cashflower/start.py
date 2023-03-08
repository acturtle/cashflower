import datetime
import importlib
import inspect
import os
import pandas as pd
import numpy as np

from .cashflow import CashflowModelError, ModelVariable, ModelPoint, Model, Constant, Runplan
from .utils import print_log


def load_settings(settings=None):
    """Load model settings.
    The function firstly reads the default settings and then overwrites these that have been defined by the user.
    The function helps with backward compatibility.
    If there is a new setting in the package, the user doesn't have to have it in the settings script.

    Parameters
    ----------
    settings : dict
        Model settings defined by the user. (Default value = None)

    Returns
    -------
    dict
    """
    if settings is None:
        settings = dict()

    initial_settings = {
        "AGGREGATE": True,
        "MULTIPROCESSING": False,
        "OUTPUT_COLUMNS": [],
        "POLICY_ID_COLUMN": "policy_id",
        "SAVE_RUNTIME": False,
        "T_CALCULATION_MAX": 1200,
        "T_OUTPUT_MAX": 1200,
    }

    for key, value in settings.items():
        initial_settings[key] = value

    return initial_settings


def get_runplan(input_members):
    """Get runplan object from input.py script.

    Parameters
    ----------
    input_members : list of tuples
        Items defined in input.py.

    Returns
    -------
    object of class Runplan
    """
    runplan = None
    for name, item in input_members:
        if isinstance(item, Runplan):
            runplan = item
            break
    return runplan


def get_modelpoints(input_members, settings):
    """Get model points from input.py script.

    Parameters
    ----------
    input_members : list of tuples
        Items defined in input.py.

    settings : dict
        Settings defined by the user.

    Returns
    -------
    Tuple, first item is a list of ModelPoint objects and second item is primary ModelPoint
    """
    modelpoint_members = [m for m in input_members if isinstance(m[1], ModelPoint)]

    policy = None
    modelpoints = []
    for name, modelpoint in modelpoint_members:
        modelpoint.name = name
        modelpoint.settings = settings
        modelpoint.initialize()
        modelpoints.append(modelpoint)
        if name == "policy":
            policy = modelpoint

    if policy is None:
        raise CashflowModelError("\nA model must have a modelpoint named 'policy'.")

    return modelpoints, policy


def get_variables(model_members, policy, settings):
    """Get model variables from input.py script.

    Parameters
    ----------
    model_members : list of tuples
        Items defined in input.py.

    policy : object of class ModelPoint
        Primary model point in the model.

    settings : dict
        Settings defined by the user.

    Returns
    -------
    List of ModelVariable objects.
    """
    variable_members = [m for m in model_members if isinstance(m[1], ModelVariable)]
    variables = []
    for name, variable in variable_members:
        variable.name = name
        variable.settings = settings
        variable.initialize(policy)
        variables.append(variable)

    # Model variables can not be overwritten by formulas with the same name
    overwritten = list(set(ModelVariable.instances) - set(variables))
    if len(overwritten) > 0:
        for item in overwritten:
            if item.assigned_formula is None:
                msg = "\nThere are two variables with the same name. Please check the 'model.py' script."
                raise CashflowModelError(msg)
        names = [item.assigned_formula.__name__ for item in overwritten]
        names_str = ", ".join(names)
        msg = f"\nThe variables with the following formulas are not correctly handled in the model: \n{names_str}"
        raise CashflowModelError(msg)

    return variables


def get_constants(model_members, policy):
    """Get constants from input.py script.

    Parameters
    ----------
    model_members : list of tuples
        Items defined in input.py.
    policy : object of class ModelPoint
        Primary model point in the model.

    Returns
    -------
    List of Constant objects.
    """
    constant_members = [m for m in model_members if isinstance(m[1], Constant)]
    constants = []
    for name, constant in constant_members:
        constant.name = name
        constant.initialize(policy)
        constants.append(constant)
    return constants


def prepare_model_input(model_name, settings, argv):
    """Initiate a Model object and run it."""
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

    # User can provide runplan version in CLI command
    if runplan is not None and len(argv) > 1:
        runplan.version = argv[1]

    return runplan, modelpoints, variables, constants


def start(model_name, settings, argv):
    """Initiate a Model object and run it."""
    settings = load_settings(settings)
    runplan, modelpoints, variables, constants = prepare_model_input(model_name, settings, argv)

    # Run model on single core and save results
    model = Model(model_name, variables, constants, modelpoints, settings)
    model.run()
    model.save()


def execute(part, model_name, settings, cpu_count, argv):
    """Execute part of the model points using multiprocessing."""
    settings = load_settings(settings)
    runplan, modelpoints, variables, constants = prepare_model_input(model_name, settings, argv)

    # Run model on multiple cores
    model = Model(model_name, variables, constants, modelpoints, settings, cpu_count)
    output = model.run(part)
    return output


def merge_and_save(outputs, settings):
    """Merge outputs from multiprocessing and save to files."""
    t_output_max = min(settings["T_OUTPUT_MAX"], settings["T_CALCULATION_MAX"])

    # Nones are returned, when number of policies < number of cpus
    outputs = [output for output in outputs if output is not None]

    # Merge outputs into one
    modelpoints = outputs[0].keys()
    model_output = {}
    for modelpoint in modelpoints:
        if settings["AGGREGATE"]:
            model_output[modelpoint] = sum(output[modelpoint] for output in outputs)
            model_output[modelpoint]["t"] = np.arange(t_output_max + 1)
        else:
            model_output[modelpoint] = pd.concat(output[modelpoint] for output in outputs)

    # Save results
    if not os.path.exists("output"):
        os.makedirs("output")

    print_log("Saving files:")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for modelpoint in modelpoints:
        filepath = f"output/{timestamp}_{modelpoint}.csv"
        print(f"{' ' * 10} {filepath}")
        model_output[modelpoint].to_csv(filepath, index=False)
