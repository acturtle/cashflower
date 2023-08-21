import datetime
import functools
import importlib
import inspect
import itertools
import multiprocessing
import networkx as nx
import os
import pandas as pd
import shutil

from .cashflow import Model, ModelPointSet, Runplan, Variable
from .error import CashflowModelError
from .graph import get_calc_direction, get_calls, get_predecessors
from .utils import print_log, replace_in_file


def create_model(model):
    """
    Create a folder structure for a model.
    Copies the whole content of the model_tpl folder and changes templates to scripts.
    """
    template_path = os.path.join(os.path.dirname(__file__), "model_tpl")
    current_path = os.getcwd()

    shutil.copytree(template_path, model)

    # Some scripts needs words replacements
    run_file = os.path.join(current_path, model, "run.py-tpl")
    replace_in_file(run_file, "{{ model }}", model)

    # Remove -tpl from template
    os.rename(run_file, run_file[:-4])


def load_settings(settings=None):
    """Add missing settings."""
    initial_settings = {
        "AGGREGATE": True,
        "MULTIPROCESSING": False,
        "OUTPUT_COLUMNS": [],
        "ID_COLUMN": "id",
        "SAVE_DIAGNOSTIC": True,
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


def get_variables(model_members, settings):
    """Get model variables from model.py script."""
    variable_members = [m for m in model_members if isinstance(m[1], Variable)]
    variables = []

    for name, variable in variable_members:
        if name == "t":
            msg = f"\nA variable can not be named '{name}' because it is a system variable. Please rename it."
            raise CashflowModelError(msg)
        variable.name = name
        variable.settings = settings
        variables.append(variable)
    return variables


def prepare_model_input(settings, argv):
    """Get input for the cash flow model."""
    input_module = importlib.import_module("input")
    model_module = importlib.import_module("model")

    # input.py contains runplan and model point sets
    input_members = inspect.getmembers(input_module)
    runplan = get_runplan(input_members)
    model_point_sets, main = get_model_point_sets(input_members, settings)

    # model.py contains model variables
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, settings)

    # User can provide runplan version in CLI command
    if runplan is not None and len(argv) > 1:
        runplan.version = argv[1]

    return runplan, model_point_sets, variables


def create_graph(variables):
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


def start_single_core(model_name, settings, argv):
    """Create and run a cash flow model."""
    runplan, model_point_sets, variables = prepare_model_input(settings, argv)
    variables = create_graph(variables)

    # Run model on single core
    model = Model(model_name, variables, model_point_sets, settings)
    model_output, runtime = model.run()
    return model_output, runtime


def start_multiprocessing(part, cpu_count, model_name, settings, argv):
    """Run subset of the model points using multiprocessing."""
    runplan, model_point_sets, variables = prepare_model_input(settings, argv)
    variables = create_graph(variables)

    # Run model on multiple cores
    model = Model(model_name, variables, model_point_sets, settings, cpu_count)
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

    # Merge or concatenate outputs into one
    if settings["AGGREGATE"] is False:
        model_output = pd.concat(part_model_outputs)
    else:
        model_output = functools.reduce(lambda x, y: x.add(y, fill_value=0), part_model_outputs)

    return model_output


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


def start(model_name, settings, argv):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    settings = load_settings(settings)
    output, diagnostic = None, None

    if settings["MULTIPROCESSING"]:
        cpu_count = multiprocessing.cpu_count()
        p = functools.partial(start_multiprocessing, cpu_count=cpu_count, model_name=model_name, settings=settings,
                              argv=argv)
        with multiprocessing.Pool(cpu_count) as pool:
            parts = pool.map(p, range(cpu_count))

        # Merge model outputs
        part_model_outputs = [p[0] for p in parts]
        output = merge_part_model_outputs(part_model_outputs, settings)

        # Merge runtimes
        if settings["SAVE_DIAGNOSTIC"]:
            part_runtimes = [p[1] for p in parts]
            diagnostic = merge_part_diagnostic(part_runtimes)
    else:
        output, diagnostic = start_single_core(model_name, settings, argv)

    # Add time column
    values = [*range(settings["T_MAX_OUTPUT"]+1)] * int(output.shape[0] / (settings["T_MAX_OUTPUT"]+1))
    output.insert(0, "t", values)

    # Save to csv files
    if not os.path.exists("output"):
        os.makedirs("output")

    if settings["SAVE_OUTPUT"]:
        print_log("Saving output:")
        filepath = f"output/{timestamp}_output.csv"
        output.to_csv(filepath, index=False)
        print(f"{' ' * 10} {filepath}")

    if settings["SAVE_DIAGNOSTIC"]:
        print_log("Saving diagnostic file:")
        filepath = f"output/{timestamp}_diagnostic.csv"
        diagnostic.to_csv(filepath, index=False)
        print(f"{' ' * 10} {filepath}")

    print_log("Finished")
    return output
