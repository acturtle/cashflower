import argparse
import datetime
import functools
import getpass
import importlib
import inspect
import itertools
import multiprocessing
import networkx as nx
import os
import pandas as pd
import shutil

from .core import ArrayVariable, Model, ModelPointSet, Runplan, Variable
from .error import CashflowModelError
from .graph import get_calc_direction, get_calls, get_predecessors
from .utils import get_git_commit_info, get_object_by_name, print_log, save_log_to_file


def create_model(model):
    """Create a folder structure for a model."""
    template_path = os.path.join(os.path.dirname(__file__), "model_tpl")
    shutil.copytree(template_path, model)


def load_settings(settings=None):
    """Add missing settings."""
    initial_settings = {
        "AGGREGATE": True,
        "GROUP_BY_COLUMN": None,
        "ID_COLUMN": "id",
        "MULTIPROCESSING": False,
        "OUTPUT_COLUMNS": [],
        "SAVE_DIAGNOSTIC": True,
        "SAVE_LOG": True,
        "SAVE_OUTPUT": True,
        "T_MAX_CALCULATION": 720,
        "T_MAX_OUTPUT": 720,
    }

    if settings is None:
        return initial_settings

    # Update with the user settings
    for key, value in settings.items():
        initial_settings[key] = value

    # Maximal output t can't exceed maximal calculation t
    if initial_settings["T_MAX_CALCULATION"] < initial_settings["T_MAX_OUTPUT"]:
        out = initial_settings["T_MAX_OUTPUT"]
        cal = initial_settings["T_MAX_CALCULATION"]
        msg = (f"T_MAX_OUTPUT ('{out}') exceeds T_MAX_CALCULATION ('{cal}'); "
               f"T_MAX_OUTPUT adjusted to match T_MAX_CALCULATION.")
        print_log(msg)
        initial_settings["T_MAX_OUTPUT"] = initial_settings["T_MAX_CALCULATION"]

    return initial_settings


def get_runplan(input_members, args):
    """Get runplan object from input.py script. Assign version if provided in the CLI command."""
    runplan = None
    for name, item in input_members:
        if isinstance(item, Runplan):
            runplan = item
            break

    if runplan is not None and args.version is not None:
        runplan.version = args.version

    return runplan


def get_model_point_sets(input_members, settings, args):
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

    if args.id is not None:
        chosen_id = str(args.id)
        main.data = main.data.loc[chosen_id]

    return model_point_sets


def get_variables(model_members, settings):
    """Get model variables from model.py script."""
    variable_members = [m for m in model_members if isinstance(m[1], Variable)]
    variables = []

    for name, variable in variable_members:
        if name == "t":
            msg = f"\nA variable can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)
        variable.name = name
        variable.t_max = settings["T_MAX_CALCULATION"]
        variables.append(variable)
    return variables


def prepare_model_input(settings, args):
    """Get input for the cash flow model."""
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


def resolve_calculation_order(variables, output_columns):
    """Determines a safe execution order for variables to avoid recursion errors."""
    # Dictionary of called functions
    calls = {}
    for variable in variables:
        calls[variable] = get_calls(variable, variables)

    # Create directed graph for all variables
    DG = nx.DiGraph()
    for variable in variables:
        DG.add_node(variable)
        for predecessor in calls[variable]:
            DG.add_edge(predecessor, variable)

    # User has chosen output so remove not needed variables
    if output_columns is not None:
        needed_variables = set()
        output_variables = [get_object_by_name(variables, name) for name in output_columns]
        for output_variable in output_variables:
            needed_variables.add(output_variable)
            needed_variables.update(get_predecessors(output_variable, DG))

        unneeded_variables = set(variables) - needed_variables
        DG.remove_nodes_from(unneeded_variables)
        variables = list(needed_variables)

    # Draw graph (debug)
    # import matplotlib.pyplot as plt
    # nx.draw(DG, with_labels=True)
    # plt.show()

    # Set calc_order in variables
    calc_order = 0
    while DG.nodes:
        nodes_without_predecessors = [node for node in DG.nodes if len(list(DG.predecessors(node))) == 0]
        if len(nodes_without_predecessors) > 0:
            for node in nodes_without_predecessors:
                calc_order += 1
                node.calc_order = calc_order
            DG.remove_nodes_from(nodes_without_predecessors)
        else:  # it's a cycle
            cycles = list(nx.simple_cycles(DG))
            cycles_without_predecessors = [c for c in cycles if len(get_predecessors(c[0], DG)) == len(c)]

            if len(cycles_without_predecessors) == 0:
                big_cycle = list(set(list(itertools.chain(*cycles))))
                cycles_without_predecessors = [big_cycle]

            for cycle_without_predecessors in cycles_without_predecessors:
                calc_order += 1
                for node in cycle_without_predecessors:
                    node.calc_order = calc_order
                    node.cycle = True
                DG.remove_nodes_from(cycle_without_predecessors)

    # Ensure that there are no ArrayVariables in cycles
    cycle_variables = [v for v in variables if v.cycle]
    for cycle_variable in cycle_variables:
        if isinstance(cycle_variable, ArrayVariable):
            msg = (f"'{cycle_variable.name}' is part of a cycle so it can't be modelled as an array variable. "
                   f"Please remove 'array=True' from the decorator and recode the variable.")
            raise CashflowModelError(msg)

    # Sort variables for calculation order
    variables = sorted(variables, key=lambda x: (x.calc_order, x.name))

    # Get calc_direction of calculation
    max_calc_order = variables[-1].calc_order
    for calc_order in range(1, max_calc_order + 1):
        # Multiple variables can have the same calc_order if they are part of the cycle
        calc_order_variables = [v for v in variables if v.calc_order == calc_order]
        calc_direction = get_calc_direction(calc_order_variables)
        for variable in calc_order_variables:
            variable.calc_direction = calc_direction

    return variables


def start_single_core(settings, args):
    """Create and run a cash flow model."""
    # Prepare model components
    print_log("Reading model components...", show_time=True)
    runplan, model_point_sets, variables = prepare_model_input(settings, args)
    output_columns = None if len(settings["OUTPUT_COLUMNS"]) == 0 else settings["OUTPUT_COLUMNS"]
    variables = resolve_calculation_order(variables, output_columns)

    # Log runplan version and number of model points
    if runplan is not None:
        print_log(f"Runplan version: {runplan.version}")
    main = get_object_by_name(model_point_sets, "main")
    print_log(f"Number of model points: {len(main)}")

    # Run model on single core
    model = Model(variables, model_point_sets, settings)
    output, runtime = model.run()
    return output, runtime


def start_multiprocessing(part, settings, args):
    """Run subset of the model points using multiprocessing."""
    cpu_count = multiprocessing.cpu_count()
    one_core = part == 0

    # Prepare model components
    print_log("Reading model components...", show_time=True, visible=one_core)
    runplan, model_point_sets, variables = prepare_model_input(settings, args)
    output_columns = None if len(settings["OUTPUT_COLUMNS"]) == 0 else settings["OUTPUT_COLUMNS"]
    variables = resolve_calculation_order(variables, output_columns)

    # Log runplan version and number of model points
    if runplan is not None:
        print_log(f"Runplan version: {runplan.version}", visible=one_core)
    main = get_object_by_name(model_point_sets, "main")
    print_log(f"Number of model points: {len(main)}", visible=one_core)
    print_log(f"Multiprocessing on {cpu_count} cores", visible=one_core)
    print_log(f"Calculation of ca. {len(main) // cpu_count} model points per core", visible=one_core)

    # Run model on multiple cores
    model = Model(variables, model_point_sets, settings)
    model_run = model.run(part)

    if model_run is None:
        part_output, part_runtime = None, None
    else:
        part_output, part_runtime = model_run
    return part_output, part_runtime


def merge_part_outputs(part_outputs, settings):
    """Merge outputs from multiprocessing and save to files."""
    # Nones are returned, when number of policies < number of cpus
    part_outputs = [po for po in part_outputs if po is not None]

    # Merge or concatenate outputs into one
    if settings["AGGREGATE"]:
        output = functools.reduce(lambda x, y: x.add(y, fill_value=0), part_outputs)
        if settings["GROUP_BY_COLUMN"] is not None:
            # group_by_column should not be added up
            output[settings["GROUP_BY_COLUMN"]] = part_outputs[0][settings["GROUP_BY_COLUMN"]]
    else:
        output = pd.concat(part_outputs)

    return output


def merge_part_diagnostic(part_diagnostic):
    # Nones are returned, when number of policies < number of cpus
    part_diagnostic = [item for item in part_diagnostic if item is not None]
    total_runtimes = sum([item["runtime"] for item in part_diagnostic])
    first = part_diagnostic[0]
    runtimes = pd.DataFrame({
        "variable": first["variable"],
        "calc_order": first["calc_order"],
        "cycle": first["cycle"],
        "calc_direction": first["calc_direction"],
        "runtime": total_runtimes
    })
    return runtimes


def run(settings=None, path=None):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    settings = load_settings(settings)
    output, diagnostic = None, None

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", "-i")
    parser.add_argument("--version", "-v")
    args = parser.parse_args()

    # Start log
    if path is not None:
        print_log(f"Model: '{os.path.basename(path)}'", show_time=True)
        print_log(f"Path: {path}")
    else:
        print_log("Model", show_time=True)
    print_log(f"Timestamp: {timestamp}")
    print_log(f"User: '{getpass.getuser()}'")
    commit = get_git_commit_info()
    if commit is not None:
        print_log(f"Git commit: {commit}")
    print_log("")

    has_arguments = any(arg_value is not None for arg_value in vars(args).values())
    if has_arguments:
        print_log("Arguments:")
        for arg_name, arg_value in vars(args).items():
            if arg_value is not None:
                print_log(f'- {arg_name}: {arg_value}')
        print_log("")

    print_log("Settings:")
    for key, value in settings.items():
        msg = f"- {key}: {value}"
        print_log(msg)
    print_log("")

    # Run on single core
    if not settings["MULTIPROCESSING"]:
        output, diagnostic = start_single_core(settings, args=args)

    # Run on multiple cores
    if settings["MULTIPROCESSING"]:
        p = functools.partial(start_multiprocessing, settings=settings, args=args)
        cpu_count = multiprocessing.cpu_count()
        with multiprocessing.Pool(cpu_count) as pool:
            parts = pool.map(p, range(cpu_count))

        # Merge model outputs
        part_outputs = [p[0] for p in parts]
        output = merge_part_outputs(part_outputs, settings)

        # Merge runtimes
        if settings["SAVE_DIAGNOSTIC"]:
            part_runtimes = [p[1] for p in parts]
            diagnostic = merge_part_diagnostic(part_runtimes)

    # Add time column
    values = [*range(settings["T_MAX_OUTPUT"]+1)] * int(output.shape[0] / (settings["T_MAX_OUTPUT"]+1))
    output.insert(0, "t", values)
    print_log("Finished!", show_time=True)
    print_log("")

    # Save to csv files
    if settings["SAVE_OUTPUT"] or settings["SAVE_DIAGNOSTIC"] or settings["SAVE_LOG"]:
        if not os.path.exists("output"):
            os.makedirs("output")

        if settings["SAVE_OUTPUT"]:
            filepath = f"output/{timestamp}_output.csv"
            print_log(f"Saving output file: {filepath}", show_time=True)
            output.to_csv(filepath, index=False)

        if settings["SAVE_DIAGNOSTIC"]:
            filepath = f"output/{timestamp}_diagnostic.csv"
            print_log(f"Saving diagnostic file: {filepath}", show_time=True)
            diagnostic.to_csv(filepath, index=False)

        if settings["SAVE_LOG"]:
            filepath = f"output/{timestamp}_log.txt"
            print_log(f"Saving log file: {filepath}", show_time=True)
            save_log_to_file(timestamp)

    print(f"{'-' * 72}\n")
    return output
