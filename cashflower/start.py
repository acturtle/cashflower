import argparse
import datetime
import functools
import getpass
import importlib
import inspect
import multiprocessing
import numpy as np
import os
import pandas as pd
import shutil
import types

from .core import Model, ModelPointSet, Runplan, StochasticVariable, Variable
from .error import CashflowModelError
from .graph import (create_directed_graph, filter_variables_and_graph, set_calc_direction, process_acyclic_nodes,
                    find_source_cycles, process_cycle)
from .utils import get_git_commit_info, get_main_model_point_set, log_message, log_messages, save_log_to_file, split_to_chunks
from .visualize import show_graph


DEFAULT_SETTINGS = {
    "GROUP_BY": None,
    "MULTIPROCESSING": False,
    "NUM_STOCHASTIC_SCENARIOS": None,
    "OUTPUT_VARIABLES": None,
    "SAVE_DIAGNOSTIC": False,
    "SAVE_LOG": False,
    "SAVE_OUTPUT": True,
    "T_MAX_CALCULATION": 720,
    "T_MAX_OUTPUT": 720,
}


def create_model(model):
    """Create a folder structure for a model.

    Args:
        model (str): The path where the folder structure should be created.

    Returns:
        None
    """
    template_path = os.path.join(os.path.dirname(__file__), "model_tpl")

    try:
        shutil.copytree(template_path, model)
    except OSError as e:
        print(f"Error: {e.filename} - {e.strerror}.")


def get_settings_changes_log(settings=None):
    """Returns a list of logs describing adjustments to the user's settings."""
    changes = []

    if settings is None:
        changes.append("* The settings are currently empty. Default settings will be applied.")
        return changes

    # Some user's settings may be missing or redundant
    missing_settings = set(DEFAULT_SETTINGS.keys()) - set(settings.keys())
    redundant_settings = set(settings.keys()) - set(DEFAULT_SETTINGS.keys())

    if missing_settings:
        changes.append(f"* Missing: {', '.join(missing_settings)}")

    if redundant_settings:
        changes.append(f"* Redundant: {', '.join(redundant_settings)}")

    # Output cannot exceed calculation
    out, cal = settings["T_MAX_OUTPUT"], settings["T_MAX_CALCULATION"]
    if out > cal:
        changes.append(f"* T_MAX_OUTPUT ('{out}') cannot exceed T_MAX_CALCULATION ('{cal}')")

    return changes


def check_settings(settings):
    # Boolean (True/False) - MULTIPROCESSING, SAVE_DIAGNOSTIC, SAVE_LOG, SAVE_OUTPUT
    for setting_name in ["MULTIPROCESSING", "SAVE_DIAGNOSTIC", "SAVE_LOG", "SAVE_OUTPUT"]:
        if not isinstance(settings[setting_name], bool):
            raise CashflowModelError(f"The {setting_name} setting must be a boolean (True or False).")

    # None or string - GROUP_BY
    if not (settings["GROUP_BY"] is None or isinstance(settings["GROUP_BY"], str)):
        raise CashflowModelError("The GROUP_BY setting must be None or a string.")

    # None or a list of strings - OUTPUT_VARIABLES
    setting = settings["OUTPUT_VARIABLES"]
    if not (setting is None or (isinstance(setting, list) and all(isinstance(item, str) for item in setting))):
        raise CashflowModelError("The OUTPUT_VARIABLES setting must be None or a list of strings.")

    # None or non-negative integer - NUM_STOCHASTIC_SCENARIOS
    setting = settings["NUM_STOCHASTIC_SCENARIOS"]
    if not (setting is None or (isinstance(setting, int) and setting >= 0)):
        raise CashflowModelError("The NUM_STOCHASTIC_SCENARIOS setting must be None or a non-negative integer.")

    # Non-negative integer - T_MAX_CALCULATION, T_MAX_OUTPUT
    for setting_name in ["T_MAX_CALCULATION", "T_MAX_OUTPUT"]:
        if not (isinstance(settings[setting_name], int) and settings[setting_name] >= 0):
            raise CashflowModelError(f"The {setting_name} setting must be a non-negative integer.")


def get_settings(settings=None):
    if settings is None:
        return DEFAULT_SETTINGS

    # Update default settings with the user's settings
    updated_settings = {key: settings.get(key, DEFAULT_SETTINGS[key]) for key in DEFAULT_SETTINGS}

    # The output time period cannot exceed the calculation time period
    updated_settings["T_MAX_OUTPUT"] = min(updated_settings["T_MAX_OUTPUT"], updated_settings["T_MAX_CALCULATION"])

    # Check if settings have been set correctly by the user
    check_settings(updated_settings)

    return updated_settings


def get_runplan(input_members):
    """
    Get runplan object from input.py script. Assign version if provided in the CLI command.

    Args:
        input_members (list): A list of tuples containing the name and instance of each input member.
        args (obj): An object containing the CLI command arguments.

    Returns:
        obj: The first Runplan object found in the input_members list, or None if no Runplan object is found.
    """
    runplan = None
    for name, item in input_members:
        if isinstance(item, Runplan):
            runplan = item
            break

    return runplan


def get_model_point_sets(input_members, settings):
    """
    Get model point set objects from the input.py script.

    Args:
        input_members (list): List of tuples containing member names and their corresponding values.
        settings (object): Settings object containing configuration for the model point sets.

    Returns:
        list: A list of initialized ModelPointSet objects.

    Raises:
        CashflowModelError: If a model point set named 'main' is not found in the input_members.
    """
    model_point_set_members = [member for member in input_members if isinstance(member[1], ModelPointSet)]

    model_point_sets = []
    for name, model_point_set in model_point_set_members:
        model_point_set.name = name
        model_point_set.settings = settings
        model_point_sets.append(model_point_set)

    # User does not have to create any model point set
    if len(model_point_set_members) == 0:
        dummy = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        dummy.settings = settings
        model_point_sets.append(dummy)

    return model_point_sets


def get_variables(model_members, settings):
    """
   Get model variables from model.py script.

   Args:
       model_members (list): A list of tuples containing the names and values of the model members.
       settings (dict): A dictionary of settings for the model.

   Returns:
       list: A list of Variable objects.

   Raises:
       CashflowModelError: If a variable is named 't' or if a stochastic variable is used without setting the number of stochastic scenarios.
   """
    variable_members = [m for m in model_members if isinstance(m[1], Variable)]
    variables = []

    for name, variable in variable_members:
        # Check names
        if name == "t" or name == "stoch":
            msg = f"\nA variable can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)

        # Initiate empty results
        variable.result = np.empty(settings["T_MAX_CALCULATION"]+1)
        if isinstance(variable, StochasticVariable):
            if settings["NUM_STOCHASTIC_SCENARIOS"] is None:
                msg = (f"\n\nThe model contains stochastic variable ('{name}')."
                       f"\nPlease set the number of stochastic scenarios ('NUM_STOCHASTIC_SCENARIOS' in 'settings.py').")
                raise CashflowModelError(msg)

            variable.result_stoch = np.empty((settings["NUM_STOCHASTIC_SCENARIOS"], settings["T_MAX_CALCULATION"]+1))

        # Add to the list
        variables.append(variable)

    return variables


def check_input(model_members, settings, model_point_sets, variables):
    # Model variables must be defined in `model.py`
    for m in model_members:
        if isinstance(m[1], types.ModuleType):
            for attr_name in dir(m[1]):
                module_var = getattr(m[1], attr_name)
                if isinstance(module_var, Variable):
                    msg = (f"\n\nIt looks like you're trying to use variables from '{m[1].__name__}'. \n"
                           f"Please import them with 'from {m[1].__name__} import *' to continue.")
                    raise CashflowModelError(msg)

    # The OUTPUT_VARIABLES setting must contain only existing variables
    variable_names = [v.name for v in variables]
    output_variable_names = settings["OUTPUT_VARIABLES"]

    if output_variable_names:
        for output_variable_name in output_variable_names:
            if output_variable_name not in variable_names:
                msg = (f"The '{output_variable_name}' is not defined in the model. "
                       f"Please check the OUTPUT_VARIABLES setting.")
                raise CashflowModelError(msg)

    # Exactly one model point set must have main = True
    count_main_true = sum(1 for model_point_set in model_point_sets if model_point_set.main)
    if count_main_true != 1:
        msg = "Exactly one ModelPointSet must have 'main' set to True."
        raise CashflowModelError(msg)

    # If there are multiple model point sets, id_column must be defined
    if len(model_point_sets) > 1:
        for model_point_set in model_point_sets:
            if model_point_set.id_column is None:
                msg = "When multiple model point sets are provided, each must have an 'id_column' defined."
                raise CashflowModelError(msg)

    # ID column must be a column in data
    for model_point_set in model_point_sets:
        if model_point_set.id_column and model_point_set.id_column not in model_point_set.data.columns:
            msg = f"\nModel point set '{model_point_set.name}' is missing the id column '{model_point_set.id_column}'."
            raise CashflowModelError(msg)

    return None


def apply_command_line_arguments(args, runplan, model_point_sets):
    # --version
    if runplan is not None and args.version is not None:
        runplan.version = args.version

    # --chunk
    if args.chunk is not None:
        main = get_main_model_point_set(model_point_sets)
        num_model_points = len(main)
        part, total = args.chunk
        assert 1 <= part <= total, f"Invalid chunk: part {part} of {total}"
        chunk_range = split_to_chunks(num_model_points, total)[part - 1]
        main.data = main.data.iloc[chunk_range[0]:chunk_range[1]]

    return runplan, model_point_sets


def get_model_input(settings, args):
    """
    Prepare the input for the cash flow model.

    Args:
        settings (dict): A dictionary of settings for the model.
        args (dict): A dictionary of arguments for the model.

    Returns:
        tuple: A tuple containing the runplan, model point sets, and variables for the cash flow model.

    Notes:
        This function imports the input and model modules, gets the members of these modules,
        and then uses these members to get the runplan, model point sets, and variables for the cash flow model.
    """
    input_module = importlib.import_module("input")
    model_module = importlib.import_module("model")

    # input.py contains runplan and model point sets
    input_members = inspect.getmembers(input_module)
    runplan = get_runplan(input_members)
    model_point_sets = get_model_point_sets(input_members, settings)

    # model.py contains model variables
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, settings)

    # Check consistency of the input
    check_input(model_members, settings, model_point_sets, variables)

    # Apply command line arguments
    runplan, model_point_sets = apply_command_line_arguments(args, runplan, model_point_sets)

    return runplan, model_point_sets, variables


def determine_calculation_order(variables, settings):
    """
    Determines a safe execution order for variables to avoid recursion errors.

    The function creates a dictionary of called functions for each variable, then creates a directed graph representing
    the relationships between variables. If output variables are specified, it filters the variables and graph
    to only include the necessary variables. It then sets the calculation order of the variables,
    handling both acyclic and cyclic relationships.
    Finally, it sorts the variables by calculation order and sets the calculation direction.

    Parameters:
    variables (list): A list of variable objects.
    settings (dict): A dictionary with model's settings.
    Returns:
    list: A list of variable objects, sorted by calculation order and with their calculation direction set.
    """
    output_variable_names = settings["OUTPUT_VARIABLES"]

    # [1] Create directed graph for all variables
    dg = create_directed_graph(variables)

    # [2] User has chosen output columns so remove unneeded variables
    if output_variable_names:
        variables, dg = filter_variables_and_graph(variables, output_variable_names, dg)

    # [3] Set calculation order of variables ('calc_order')
    calc_order = 0
    while dg.nodes:
        nodes_without_predecessors, has_acyclic_nodes = process_acyclic_nodes(dg)

        # [3A] Acyclic
        if has_acyclic_nodes:
            for node in nodes_without_predecessors:
                calc_order += 1
                node.calc_order = calc_order
            dg.remove_nodes_from(nodes_without_predecessors)

        # [3B] Cyclic
        else:
            # CASE B: Cyclic dependencies - find and process cycles
            cycles_without_predecessors = find_source_cycles(dg)

            # Process each cycle found
            for cycle in cycles_without_predecessors:
                calc_order = process_cycle(cycle, calc_order)
                dg.remove_nodes_from(cycle)

    # [4] Sort variables for calculation order
    variables = sorted(variables, key=lambda x: (x.calc_order, x.cycle_order, x.name))

    # [5] Set calculation direction of calculation ('calc_direction' attribute)
    variables = set_calc_direction(variables)

    return variables


def start_single_core(settings, args):
    """
    Create and run a cash flow model on a single core.

    Args:
        settings (dict): Model settings.
        args (dict): Additional arguments.

    Returns:
        tuple: A tuple containing the model output and runtime.
    """
    # Prepare model components
    log_message("Reading model components...", show_time=True)
    runplan, model_point_sets, variables = get_model_input(settings, args)
    variables = determine_calculation_order(variables, settings)

    # Log runplan version and number of model points
    if runplan is not None:
        log_message(f"Runplan version: {runplan.version}")
    main = get_main_model_point_set(model_point_sets)
    log_message(f"Number of model points: {len(main)}")

    # Run model on single core
    model = Model(variables, model_point_sets, settings)
    output, runtime = model.run()
    return output, runtime


def start_multiprocessing(part, settings, args):
    """
    Run subset of the model points using multiprocessing.

    Args:
        part (int): The part of the model points to run.
        settings (dict): The model settings.
        args (object): The command line arguments.

    Returns:
        tuple: A tuple containing the output and runtime of the model run.
    """
    cpu_count = multiprocessing.cpu_count()
    one_core = part == 0

    # Prepare model components
    log_message("Reading model components...", show_time=True, print_and_save=one_core)
    runplan, model_point_sets, variables = get_model_input(settings, args)
    variables = determine_calculation_order(variables, settings)

    # Log runplan version and number of model points
    if runplan is not None:
        log_message(f"Runplan version: {runplan.version}", print_and_save=one_core)
    main = get_main_model_point_set(model_point_sets)
    log_message(f"Number of model points: {len(main)}", print_and_save=one_core)
    log_message(f"Multiprocessing on {cpu_count} cores", print_and_save=one_core)
    log_message(f"Calculation of ca. {len(main) // cpu_count} model points per core", print_and_save=one_core)

    # Run model on multiple cores
    model = Model(variables, model_point_sets, settings)
    model_run = model.run(part)

    if model_run is None:
        part_output, part_runtime = None, None
    else:
        part_output, part_runtime = model_run
    return part_output, part_runtime


def merge_part_outputs(part_outputs, settings):
    """
    Merge outputs from multiprocessing.

    Args:
        part_outputs (list): A list of outputs from multiprocessing.
        settings (dict): A dictionary of settings.

    Returns:
        pandas.DataFrame: The merged output.
    """
    # Nones are returned, when number of policies < number of cpus
    part_outputs = [part_output for part_output in part_outputs if part_output is not None]

    # Merge or concatenate outputs into one
    output = functools.reduce(lambda x, y: x.add(y, fill_value=0), part_outputs)
    if settings["GROUP_BY"] is not None:
        # group_by column should not be added up
        output[settings["GROUP_BY"]] = part_outputs[0][settings["GROUP_BY"]]

    return output


def merge_part_diagnostic(part_diagnostic):
    # Nones are returned, when number of policies < number of cpus
    part_diagnostic = [item for item in part_diagnostic if item is not None]
    total_runtimes = sum([item["runtime"] for item in part_diagnostic])
    diagnostic = part_diagnostic[0]
    diagnostic["runtime"] = total_runtimes
    return diagnostic


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        args: The parsed arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--version", "-v", type=int, help="Run a specific version")
    parser.add_argument("--chunk", nargs=2, type=int, metavar=("PART", "TOTAL"),
                        help="Select PART out of TOTAL chunks of model points")
    parser.add_argument("--graph", "-g", action="store_true",
                        help="Show interactive graph visualization of variable dependencies")

    args, unknown = parser.parse_known_args()

    return args, unknown


def run_multi_core(settings, args):
    """
    Run the model on multiple cores.

    Args:
        settings (dict): A dictionary containing the settings for the model.
        args (argparse.Namespace): The arguments passed to the script.

    Returns:
        tuple: A tuple containing the output and diagnostic results.
    """
    process_func = functools.partial(start_multiprocessing, settings=settings, args=args)
    cpu_count = multiprocessing.cpu_count()
    with multiprocessing.Pool(cpu_count) as pool:
        parts = pool.map(process_func, range(cpu_count))

    # Merge model outputs
    part_outputs = [part[0] for part in parts]
    output = merge_part_outputs(part_outputs, settings)

    # Merge runtimes
    part_diagnostic = [part[1] for part in parts]
    diagnostic = merge_part_diagnostic(part_diagnostic)

    return output, diagnostic


def save_results(timestamp, output, diagnostic, settings):
    """
    Save the output, diagnostic, and log files based on the settings.

    Args:
        timestamp (str): The timestamp to use in the filenames.
        output (pandas.DataFrame): The output data to save.
        diagnostic (pandas.DataFrame): The diagnostic data to save.
        settings (dict): A dictionary containing the settings.
    """
    if not (settings["SAVE_OUTPUT"] or settings["SAVE_DIAGNOSTIC"] or settings["SAVE_LOG"]):
        return None

    if not os.path.exists("output"):
        os.makedirs("output")

    if settings["SAVE_OUTPUT"] and output is not None:
        filepath = f"output/{timestamp}_output.csv"
        log_message(f"Saving output file: {filepath}", show_time=True)
        output.to_csv(filepath, index=False)

    if settings["SAVE_DIAGNOSTIC"] and diagnostic is not None:
        filepath = f"output/{timestamp}_diagnostic.csv"
        log_message(f"Saving diagnostic file: {filepath}", show_time=True)
        diagnostic.to_csv(filepath, index=False)

    if settings["SAVE_LOG"]:
        filepath = f"output/{timestamp}.log"
        log_message(f"Saving log file: {filepath}", show_time=True)
        save_log_to_file(timestamp)


def log_run_info(timestamp, path, args, settings_changes, settings):
    """
    Logs information about the current run.

    Args:
        timestamp (str): The timestamp of the run.
        path (str): The path to the model.
        args (argparse.Namespace): The command line arguments.
        settings_changes (list): Changes to the settings provided by the user.
        settings (dict): The settings for the run.

    Returns:
        None
    """
    # Log model info
    if path is not None:
        log_message(f"Model: '{os.path.basename(path)}'", show_time=True)
        log_message(f"Path: {path}")
    else:
        log_message("Model", show_time=True)
    log_message(f"Timestamp: {timestamp}")
    log_message(f"User: '{getpass.getuser()}'")
    commit = get_git_commit_info()
    if commit is not None:
        log_message(f"Git commit: {commit}")
    log_message("")

    # Log command line arguments
    has_arguments = any(arg_value is not None for arg_value in vars(args).values())
    if has_arguments:
        log_message("Arguments:")
        for arg_name, arg_value in vars(args).items():
            if arg_value is not None:
                log_message(f'- {arg_name}: {arg_value}')
        log_message("")

    # Log settings
    if settings_changes:
        log_message("Changes to user's settings:")
        for change in settings_changes:
            log_message(change)
        log_message("")

    log_message("Run settings:")
    for key, value in settings.items():
        msg = f"- {key}: {value}"
        log_message(msg)
    log_message("")

    return None


def run(settings=None, path=None):
    """
    Run the model with given settings and path.

    Args:
        settings (dict, optional): Dictionary containing the settings. Defaults to None.
        path (str, optional): Path where the model results will be saved. Defaults to None.

    Returns:
        pandas.DataFrame: The output of the modl.
    """
    user_settings = settings
    settings = get_settings(user_settings)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output = None
    diagnostic = None

    try:
        args, _ = parse_arguments()

        # Handle graph visualization
        if args.graph:
            runplan, model_point_sets, variables = get_model_input(settings, args)
            dg = create_directed_graph(variables)

            print(f"Visualizing {len(variables)} variables...")
            show_graph(dg)
            return None, None, []

        settings_changes_log = get_settings_changes_log(settings)
        log_run_info(timestamp, path, args, settings_changes_log, settings)

        # Run on single or multiple cores
        if not settings["MULTIPROCESSING"]:
            output, diagnostic = start_single_core(settings, args=args)
        else:
            output, diagnostic = run_multi_core(settings, args)

        # Add time column
        values = [*range(settings["T_MAX_OUTPUT"]+1)] * int(output.shape[0] / (settings["T_MAX_OUTPUT"]+1))
        output.insert(0, "t", values)

        log_message("Finished.", show_time=True)
        log_message("")
    except Exception as e:
        log_message(f"An error occurred: {str(e)}", show_time=True)
        raise
    finally:
        # Save to files
        save_results(timestamp, output, diagnostic, settings)

    print(f"{'-' * 72}\n")
    return output, diagnostic, log_messages
