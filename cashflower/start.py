import datetime
import functools
import importlib
import inspect
import multiprocessing
import os
import pandas as pd
import shutil

from .cashflow import CashflowModelError, ModelVariable, ModelPointSet, Model, Constant, Runplan, Variable
from .utils import print_log, replace_in_file


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
        "T_MAX_CALCULATION": 1200,
        "T_MAX_OUTPUT": 1200,
    }

    if settings is None:
        return initial_settings

    # Update with the user settings
    for key, value in settings.items():
        initial_settings[key] = value

    # Maximal output t can't exceed maximal calculation t
    if initial_settings["T_MAX_CALCULATION"] < initial_settings["T_MAX_OUTPUT"]:
        initial_settings["T_MAX_OUTPUT"] = initial_settings["T_MAX_CALCULATION"]
        msg = "The T_MAX_CALCULATION setting is greater than the T_MAX_OUTPUT setting. " \
              "T_MAX_OUTPUT has been set to T_MAX_CALCULATION."
        print_log(msg)

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


def get_variables_new(model_members, main, settings):
    """Get model variables from model.py script."""
    variable_members = [m for m in model_members if isinstance(m[1], Variable)]
    variables = []

    for name, variable in variable_members:
        if name in ["t", "r"]:
            msg = f"\nA variable can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)
        variable.name = name
        variable.settings = settings
        variables.append(variable)
    return variables


def get_variables(model_members, main, settings):
    """Get model variables from model.py script."""
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
    # variables = get_variables(model_members, main, settings)
    variables = get_variables_new(model_members, main, settings)
    constants = get_constants(model_members, main)

    # User can provide runplan version in CLI command
    if runplan is not None and len(argv) > 1:
        runplan.version = argv[1]

    return runplan, model_point_sets, variables, constants


def dict_to_csv(_dict, timestamp):
    if not os.path.exists("output"):
        os.makedirs("output")

    for key in _dict:
        filepath = f"output/{timestamp}_{key}.csv"
        data = _dict.get(key)
        data.to_csv(filepath, index=False)
        print(f"{' ' * 10} {filepath}")

    return None


def df_to_csv(df, timestamp):
    df.to_csv(f"output/{timestamp}_runtime.csv", index=False)
    print(f"{' ' * 10} output/{timestamp}_runtime.csv")
    return None


def start_single_core(model_name, settings, argv):
    """Create and run a cash flow model."""
    runplan, model_point_sets, variables, constants = prepare_model_input(model_name, settings, argv)

    # Run model on single core
    model = Model(model_name, variables, constants, model_point_sets, settings)
    model_output, runtime = model.run()
    return model_output, runtime


def start_multiprocessing(part, cpu_count, model_name, settings, argv):
    """Run subset of the model points using multiprocessing."""
    runplan, model_point_sets, variables, constants = prepare_model_input(model_name, settings, argv)

    # Run model on multiple cores
    model = Model(model_name, variables, constants, model_point_sets, settings, cpu_count)

    output = model.run(part)
    if output is None:
        part_model_output, part_runtime = None, None
    else:
        part_model_output, part_runtime = output
    return part_model_output, part_runtime


def merge_part_model_outputs(part_model_outputs, settings):
    """Merge outputs from multiprocessing and save to files."""
    # Nones are returned, when number of policies < number of cpus
    part_model_outputs = [pmo for pmo in part_model_outputs if pmo is not None]
    first = part_model_outputs[0]

    # Merge outputs into one
    model_output = {}
    for key in first.keys():
        if settings["AGGREGATE"]:
            model_output[key] = sum(pmo[key] for pmo in part_model_outputs)
        else:
            model_output[key] = pd.concat(pmo[key] for pmo in part_model_outputs)
    return model_output


def merge_part_runtimes(part_runtimes):
    total_runtimes = sum([pr["runtime"] for pr in part_runtimes])
    first = part_runtimes[0]
    runtimes = pd.DataFrame({
        "component": first["component"],
        "runtime": total_runtimes
    })
    return runtimes


def start(model_name, settings, argv):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    settings = load_settings(settings)

    if settings["MULTIPROCESSING"]:
        cpu_count = multiprocessing.cpu_count()
        p = functools.partial(start_multiprocessing, cpu_count=cpu_count, model_name=model_name, settings=settings,
                              argv=argv)
        with multiprocessing.Pool(cpu_count) as pool:
            parts = pool.map(p, range(cpu_count))
        part_model_outputs = [p[0] for p in parts]
        output = merge_part_model_outputs(part_model_outputs, settings)
        if settings["SAVE_RUNTIME"]:
            part_runtimes = [p[1] for p in parts]
            runtime = merge_part_runtimes(part_runtimes)
    else:
        output, runtime = start_single_core(model_name, settings, argv)

    # Add time column
    for key in output.keys():
        values = [*range(settings["T_MAX_OUTPUT"]+1)] * int(output[key].shape[0] / (settings["T_MAX_OUTPUT"]+1))
        output[key].insert(0, "t", values)

    if settings["SAVE_OUTPUT"]:
        print_log("Saving results:")
        dict_to_csv(output, timestamp)

    if settings["SAVE_RUNTIME"]:
        print_log("Saving runtime:")
        df_to_csv(runtime, timestamp)

    print_log("Finished")
    return output
