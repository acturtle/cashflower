import argparse
import datetime
import functools
import getpass
import importlib
import inspect
import multiprocessing
import networkx as nx
import numpy as np
import os
import shutil

from .core import ArrayVariable, Model, ModelPointSet, Runplan, StochasticVariable, Variable
from .error import CashflowModelError
from .graph import create_directed_graph, filter_variables_and_graph, get_calls, get_predecessors, set_calc_direction
from .utils import get_git_commit_info, get_object_by_name, log_message, save_log_to_file


DEFAULT_SETTINGS = {
        "GROUP_BY": None,
        "ID_COLUMN": "id",
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


def log_settings_changes(settings=None):
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


def get_settings(settings=None):
    if settings is None:
        return DEFAULT_SETTINGS

    # Update default settings with the user's settings
    updated_settings = {key: settings.get(key, DEFAULT_SETTINGS[key]) for key in DEFAULT_SETTINGS}

    # The output time period cannot exceed the calculation time period
    updated_settings["T_MAX_OUTPUT"] = min(updated_settings["T_MAX_OUTPUT"], updated_settings["T_MAX_CALCULATION"])

    return updated_settings


def get_runplan(input_members, args):
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

    if runplan is not None and args.version is not None:
        runplan.version = args.version

    return runplan


def get_model_point_sets(input_members, settings, args):
    """
    Get model point set objects from the input.py script.

    Args:
        input_members (list): List of tuples containing member names and their corresponding values.
        settings (object): Settings object containing configuration for the model point sets.
        args (object): Arguments object containing command line arguments.

    Returns:
        list: A list of initialized ModelPointSet objects.

    Raises:
        CashflowModelError: If a model point set named 'main' is not found in the input_members.
    """
    model_point_set_members = [member for member in input_members if isinstance(member[1], ModelPointSet)]

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
        raise CashflowModelError("\nA model must have a model point set named 'main'. "
                                 "Please check your input.py script.")

    if args.id is not None:
        chosen_id = str(args.id)
        main.data = main.data.loc[chosen_id]

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
        # Set name
        if name == "t":
            msg = f"\nA variable can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)
        variable.name = name

        # Initiate empty results
        variable.result = np.empty(settings["T_MAX_CALCULATION"]+1)
        if isinstance(variable, StochasticVariable):
            if settings["NUM_STOCHASTIC_SCENARIOS"] is None:
                msg = (f"\n\nThe model contains stochastic variable ('{name}')."
                       f"\nPlease set the number of stochastic scenarios ('NUM_STOCHASTIC_SCENARIOS' in 'settings.py').")
                raise CashflowModelError(msg)

            variable.result_stoch = np.empty((settings["NUM_STOCHASTIC_SCENARIOS"], settings["T_MAX_CALCULATION"]+1))

        variables.append(variable)
    return variables


def prepare_model_input(settings, args):
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
    runplan = get_runplan(input_members, args)
    model_point_sets = get_model_point_sets(input_members, settings, args)

    # model.py contains model variables
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, settings)

    return runplan, model_point_sets, variables


def check_for_array_variables_in_cycle(cycle):
    for variable in cycle:
        if isinstance(variable, ArrayVariable):
            msg = (f"Variable '{variable.name}' is part of a cycle so it can't be modelled as an array variable."
                   f"\nCycle: {cycle}"
                   f"\nPlease remove 'array=True' from the decorator and recode the variable.")
            raise CashflowModelError(msg)


def set_cycle_order(dg_cycle):
    cycle_order = 0
    while dg_cycle.nodes:
        cycle_nodes_without_predecessors = [cn for cn in dg_cycle.nodes if len(list(dg_cycle.predecessors(cn))) == 0]
        if len(cycle_nodes_without_predecessors) > 0:
            for node in cycle_nodes_without_predecessors:
                cycle_order += 1
                node.cycle_order = cycle_order
            dg_cycle.remove_nodes_from(cycle_nodes_without_predecessors)
        else:
            cycle_variable_nodes = [node.name for node in dg_cycle.nodes]
            msg = (f"Circular relationship without time step difference is not allowed. "
                   f"Please review variables: {cycle_variable_nodes}."
                   f"\nIf circular relationship without time step difference is necessary in your project, "
                   f"please raise it on: github.com/acturtle/cashflower")
            raise CashflowModelError(msg)


def resolve_calculation_order(variables, output_variable_names):
    """
    Determines a safe execution order for variables to avoid recursion errors.

    This function takes a list of variables and an optional list of output columns as input.
    It first creates a dictionary of called functions for each variable, then creates a directed graph representing
    the relationships between variables. If output columns are specified, it filters the variables and graph
    to only include the necessary variables. It then sets the calculation order of the variables,
    handling both acyclic and cyclic relationships.
    Finally, it sorts the variables by calculation order and sets the calculation direction.

    Parameters:
    variables (list): A list of variable objects.
    output_columns (list, optional): A list of output column names. If specified, only variables that are needed for
        these columns will be included in the calculation order.

    Returns:
    list: A list of variable objects, sorted by calculation order and with their calculation direction set.
    """
    # [1] Dictionary of called functions (key = variable; value = other variables called by it)
    calls = {}
    for variable in variables:
        calls[variable] = get_calls(variable, variables)

    # [2] Create directed graph for all variables
    dg = create_directed_graph(variables, calls)

    # Debug
    # import matplotlib.pyplot as plt
    # nx.draw(dg, with_labels=True)
    # plt.show()

    # [3] User has chosen output columns so remove unneeded variables
    if output_variable_names is not None:
        variables, dg = filter_variables_and_graph(variables, output_variable_names, dg)

    # [4] Set calculation order of variables ('calc_order')
    calc_order = 0
    while dg.nodes:
        nodes_without_predecessors = [n for n in dg.nodes if len(list(dg.predecessors(n))) == 0]

        # [4a] Acyclic - there are variables without any predecessors
        if len(nodes_without_predecessors) > 0:
            for node in nodes_without_predecessors:
                calc_order += 1
                node.calc_order = calc_order
            dg.remove_nodes_from(nodes_without_predecessors)

        # [4b] Cyclic - there is a cyclic relationship between variables
        else:
            cycles = list(nx.simple_cycles(dg))

            cycles_without_predecessors = [c for c in cycles if len(get_predecessors(c[0], dg)) == len(c)]

            # Graph contains strongly connected components (SCC)
            if len(cycles_without_predecessors) == 0:
                # Find strongly connected components
                sccs = list(nx.strongly_connected_components(dg))

                # Find source SCC
                for scc in sccs:
                    has_incoming_edge = False
                    for node in scc:
                        for edge in dg.in_edges(node):
                            if edge[0] not in scc:
                                has_incoming_edge = True
                                break
                        if has_incoming_edge:
                            break
                    if not has_incoming_edge:
                        scc = sorted(list(scc))
                        cycles_without_predecessors = [scc]

            for cycle in cycles_without_predecessors:
                # Ensure that there are no ArrayVariables in cycles
                check_for_array_variables_in_cycle(cycle)

                # Set the calculation order within the cycle ('cycle_order')
                calls_t = {}  # dictionary of called functions but only for the same time period ("t")
                for variable in cycle:
                    calls_t[variable] = get_calls(variable, cycle, argument_t_only=True)
                dg_cycle = create_directed_graph(cycle, calls_t)
                set_cycle_order(dg_cycle)

                # All the variables from a cycle have the same 'calc_order' value
                calc_order += 1
                for node in cycle:
                    node.calc_order = calc_order
                    node.cycle = True
                dg.remove_nodes_from(cycle)

    # [5] Sort variables for calculation order
    variables = sorted(variables, key=lambda x: (x.calc_order, x.cycle_order, x.name))

    # [6] Set calculation direction of calculation ('calc_direction' attribute)
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
    runplan, model_point_sets, variables = prepare_model_input(settings, args)
    output_variable_names = settings["OUTPUT_VARIABLES"]
    variables = resolve_calculation_order(variables, output_variable_names)

    # Log runplan version and number of model points
    if runplan is not None:
        log_message(f"Runplan version: {runplan.version}")
    main = get_object_by_name(model_point_sets, "main")
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
    runplan, model_point_sets, variables = prepare_model_input(settings, args)
    output_variables = settings["OUTPUT_VARIABLES"]
    variables = resolve_calculation_order(variables, output_variables)

    # Log runplan version and number of model points
    if runplan is not None:
        log_message(f"Runplan version: {runplan.version}", print_and_save=one_core)
    main = get_object_by_name(model_point_sets, "main")
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

    parser.add_argument("--id", "-i", help="Run a specific model point.")
    parser.add_argument("--version", "-v", help="Run a specific version.")

    return parser.parse_args()


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
    if settings["SAVE_DIAGNOSTIC"]:
        part_diagnostic = [part[1] for part in parts]
        diagnostic = merge_part_diagnostic(part_diagnostic)
    else:
        diagnostic = None

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

    if settings["SAVE_OUTPUT"]:
        filepath = f"output/{timestamp}_output.csv"
        log_message(f"Saving output file: {filepath}", show_time=True)
        output.to_csv(filepath, index=False)

    if settings["SAVE_DIAGNOSTIC"]:
        filepath = f"output/{timestamp}_diagnostic.csv"
        log_message(f"Saving diagnostic file: {filepath}", show_time=True)
        diagnostic.to_csv(filepath, index=False)

    if settings["SAVE_LOG"]:
        filepath = f"output/{timestamp}_log.txt"
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
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    settings_changes = log_settings_changes(settings)
    settings = get_settings(settings)
    args = parse_arguments()
    log_run_info(timestamp, path, args, settings_changes, settings)

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

    # Save to csv files
    save_results(timestamp, output, diagnostic, settings)

    print(f"{'-' * 72}\n")
    return output
