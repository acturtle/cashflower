import datetime
import functools
import importlib
import inspect
import multiprocessing
import numpy as np
import os
import pandas as pd
import shutil

from .cashflow import CashflowModelError, ModelVariable, ModelPointSet, Model, Constant, Runplan
from .utils import replace_in_file, print_log


def create_model(model):
    """Create a folder structure for a model.

    Copies the whole content of the model_tpl folder and changes templates to scripts.

    Parameters
    ----------
    model : str
        Name of the model to be added.

    """
    template_path = os.path.join(os.path.dirname(__file__), "model_tpl")
    current_path = os.getcwd()

    shutil.copytree(template_path, model)

    # Some scripts needs words replacements
    run_file = os.path.join(current_path, model, "run.py-tpl")
    model_file = os.path.join(current_path, model, "model.py-tpl")
    replace_in_file(run_file, "{{ model }}", model)
    replace_in_file(model_file, "{{ model }}", model)

    # Remove -tpl from template
    os.rename(run_file, run_file[:-4])
    os.rename(model_file, model_file[:-4])


def load_settings(settings=None):
    """Add missing settings."""
    initial_settings = {
        "AGGREGATE": True,
        "MULTIPROCESSING": False,
        "OUTPUT_COLUMNS": [],
        "ID_COLUMN": "id",
        "SAVE_OUTPUT": True,
        "SAVE_RUNTIME": False,
        "T_CALCULATION_MAX": 1200,
        "T_OUTPUT_MAX": 1200,
    }

    if settings is None:
        return initial_settings

    for key, value in settings.items():
        initial_settings[key] = value

    return initial_settings


def get_runplan(input_members):
    """Get runplan object from input.py script."""
    runplan = None
    for name, item in input_members:
        if isinstance(item, Runplan):
            runplan = item
            break
    return runplan


def get_model_point_sets(input_members, settings):
    """Get model point set objects from input.py script."""
    model_point_set_members = [m for m in input_members if isinstance(m[1], ModelPointSet)]

    main = None
    model_point_sets = []
    for name, model_point_set in model_point_set_members:
        model_point_set.name = name
        model_point_set.settings = settings
        model_point_set.initialize()
        model_point_sets.append(model_point_set)
        if name == "main":
            main = model_point_set

    if main is None:
        raise CashflowModelError("\nA model must have a model point set named 'main'.")

    return model_point_sets, main


def get_variables(model_members, main, settings):
    """Get model variables from input.py script."""
    variable_members = [m for m in model_members if isinstance(m[1], ModelVariable)]
    variables = []

    for name, variable in variable_members:
        if name in ["t", "r"]:
            msg = f"\nA model component can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)
        variable.name = name
        variable.settings = settings
        variable.initialize(main)
        variables.append(variable)
    return variables


def get_constants(model_members, main):
    """Get constants from input.py script."""
    constant_members = [m for m in model_members if isinstance(m[1], Constant)]
    constants = []
    for name, constant in constant_members:
        if name in ["t", "r"]:
            msg = f"\nA model component can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)
        constant.name = name
        constant.initialize(main)
        constants.append(constant)
    return constants


def prepare_model_input(model_name, settings, argv):
    """Get input for the cash flow model."""
    input_module = importlib.import_module(model_name + ".input")
    model_module = importlib.import_module(model_name + ".model")

    # input.py contains runplan and model point sets
    input_members = inspect.getmembers(input_module)
    runplan = get_runplan(input_members)
    model_point_sets, main = get_model_point_sets(input_members, settings)

    # model.py contains model variables and constants
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, main, settings)
    constants = get_constants(model_members, main)

    # User can provide runplan version in CLI command
    if runplan is not None and len(argv) > 1:
        runplan.version = argv[1]

    return runplan, model_point_sets, variables, constants


def start_single_core(model_name, settings, argv):
    """Create, run and save results of a cash flow model."""
    settings = load_settings(settings)
    runplan, model_point_sets, variables, constants = prepare_model_input(model_name, settings, argv)

    # Run model on single core and save results
    model = Model(model_name, variables, constants, model_point_sets, settings)
    output = model.run()
    model.save()
    return output


def execute_multiprocessing(part, model_name, settings, cpu_count, argv):
    """Run subset of the model points using multiprocessing."""
    runplan, model_point_sets, variables, constants = prepare_model_input(model_name, settings, argv)

    # Run model on multiple cores
    model = Model(model_name, variables, constants, model_point_sets, settings, cpu_count)
    output = model.run(part)
    return output


def merge_and_save_multiprocessing(part_outputs, settings):
    """Merge outputs from multiprocessing and save to files."""
    t_output_max = min(settings["T_OUTPUT_MAX"], settings["T_CALCULATION_MAX"])

    # Nones are returned, when number of policies < number of cpus
    part_outputs = [part_output for part_output in part_outputs if part_output is not None]

    # Merge outputs into one
    model_point_set_names = part_outputs[0].keys()
    model_output = {}
    for model_point_set_name in model_point_set_names:
        if settings["AGGREGATE"]:
            model_output[model_point_set_name] = sum(part_output[model_point_set_name] for part_output in part_outputs)
            model_output[model_point_set_name]["t"] = np.arange(t_output_max + 1)
        else:
            model_output[model_point_set_name] = pd.concat(part_output[model_point_set_name] for part_output in part_outputs)

    if not os.path.exists("output"):
        os.makedirs("output")

    # Save output to csv
    if settings["SAVE_OUTPUT"]:
        print_log("Saving output:")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        for model_point_set_name in model_point_set_names:
            filepath = f"output/{timestamp}_{model_point_set_name}.csv"

            column_names = [col for col in model_output[model_point_set_name].columns.values.tolist() if col not in ["t", "r"]]
            if len(column_names) > 0:
                print(f"{' ' * 10} {filepath}")
                model_output[model_point_set_name].to_csv(filepath, index=False)

    print_log("Finished")
    return model_output


def start(model_name, settings, argv):
    settings = load_settings(settings)

    if settings.get("MULTIPROCESSING"):
        cpu_count = multiprocessing.cpu_count()
        p = functools.partial(execute_multiprocessing, model_name=model_name, settings=settings, cpu_count=cpu_count, argv=argv)
        with multiprocessing.Pool(cpu_count) as pool:
            part_outputs = pool.map(p, range(cpu_count))
        output = merge_and_save_multiprocessing(part_outputs, settings)
    else:
        output = start_single_core(model_name, settings, argv)

    return output
