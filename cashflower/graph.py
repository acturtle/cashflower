import ast
import inspect
import networkx as nx

from queue import Queue

from .error import CashflowModelError
from .utils import get_object_by_name


def create_directed_graph(variables, calls):
    """
    Create a directed graph based on a list of variables and a dictionary of calls.

    Parameters:
        variables (list): A list of variables to be used as nodes in the graph.
        calls (dict): A dictionary where the keys are variables and the values are lists of variables that the key variable calls.

    Returns:
        nx.DiGraph: A directed graph representing the calls between variables.
    """
    dg = nx.DiGraph()
    for variable in variables:
        dg.add_node(variable)
        for predecessor in calls[variable]:
            dg.add_edge(predecessor, variable)
    return dg


def filter_variables_and_graph(output_columns, variables, dg):
    """Select only variables and nodes that are required by the user."""
    needed_variables = set()
    output_variables = [get_object_by_name(variables, name) for name in output_columns]

    for output_variable in output_variables:
        needed_variables.add(output_variable)
        needed_variables.update(get_predecessors(output_variable, dg))

    unneeded_variables = set(variables) - needed_variables
    dg.remove_nodes_from(unneeded_variables)
    variables = list(needed_variables)
    return variables, dg


def get_calls(variable, variables, argument_t_only=False):
    """List variables called by the given variable.

    If argument_t_only is set to True, then filter only variables called with "t" (used for cycles).
    For example:
    - return my_variable(t) --> is added
    - return my_variable(t-1) --> is omitted

    Debug: print("\n", ast.dump(node, indent=2))
    """
    call_names = []
    variable_names = [variable.name for variable in variables]
    node = ast.parse(inspect.getsource(variable.func))

    for subnode in ast.walk(node):
        # Variable calls other variable directly (e.g. projection_year(t))
        if isinstance(subnode, ast.Call):
            if isinstance(subnode.func, ast.Name):
                if subnode.func.id in variable_names:
                    raise_error_if_incorrect_argument(subnode, variable)
                    # Add variable regardless of its argument
                    if argument_t_only is False:
                        call_names.append(subnode.func.id)
                    # Add variable only if it calls "t"
                    else:
                        if isinstance(subnode.args[0], ast.Name):
                            call_names.append(subnode.func.id)

    calls = [get_object_by_name(variables, call_name) for call_name in call_names if call_name != variable.name]
    return calls


def get_calc_direction(variables):
    """Set calculation direction to irrelevant [0] / forward [1] / backward [-1]"""
    # For non-cycle => single variable, for cycle => variables from the cycle
    variable_names = [variable.name for variable in variables]

    calc_directions = set()
    for variable in variables:
        node = ast.parse(inspect.getsource(variable.func))
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Name):  # not a method
                    if subnode.func.id in variable_names:  # single variable or another variable in the cycle
                        arg = subnode.args[0]
                        if isinstance(arg, ast.BinOp):
                            # Does it call t+... or t-...?
                            check1 = isinstance(arg.left, ast.Name) and arg.left.id == "t"
                            check2 = isinstance(arg.op, ast.Add)
                            check3 = isinstance(arg.op, ast.Sub)

                            if check1 and check2:
                                calc_directions.add(-1)

                            if check1 and check3:
                                calc_directions.add(1)

    # One calculation direction
    if len(calc_directions) == 1:
        return list(calc_directions)[0]

    # Bidirectional variables are not allowed
    if len(calc_directions) > 1:
        msg = (f"Bidirectional recursion is not allowed. Please review variables: '{', '.join(variable_names)}'."
               f"\nIf bidirectional recursion is necessary in your project, please raise it on: github.com/acturtle/cashflower")
        raise CashflowModelError(msg)

    return 0


def get_predecessors(node, dg):
    """Get list of predecessors and their predecessors and their..."""
    queue = Queue()
    visited = []

    queue.put(node)
    visited.append(node)

    while not queue.empty():
        node = queue.get()
        for child in dg.predecessors(node):
            if child not in visited:
                queue.put(child)
                visited.append(child)

    return visited


def raise_error_if_incorrect_argument(subnode, variable):
    """Model variables call other variables.
    Called variables can have maximally two arguments (for time and stochastic scenario).

    The first argument should be:
    - t               | my_variable(t, ...)
    - t+...           | my_variable(t+1, ...)
    - t-...           | my_variable(t-1, ...)
    - constant value  | my_variable(0, ...)
    """
    # More than 2 arguments
    if len(subnode.args) > 2:
        msg = (f"\n\nModel variable can have maximally two arguments. "
               f"\nPlease review the call of '{subnode.func.id}' in '{variable.name}'.")
        raise CashflowModelError(msg)

    # Either 1 or 2 arguments
    if len(subnode.args) > 0:
        arg = subnode.args[0]
        msg = f"\n\nPlease review the calls of '{subnode.func.id}'. The first argument of a model variable can be only:\n" \
              f"- t,\n" \
              f"- t plus/minus integer (e.g. t+1 or t-12),\n" \
              f"- a non-negative integer (e.g. 0 or 12)."

        # The model variable calls a variable
        if isinstance(arg, ast.Name):
            if not arg.id == "t":
                raise CashflowModelError(msg)

        # The model variable calls an operation
        if isinstance(arg, ast.BinOp):
            check1 = isinstance(arg.left, ast.Name) and arg.left.id == "t"
            check2 = isinstance(arg.op, ast.Add) or isinstance(arg.op, ast.Sub)
            check3 = isinstance(arg.right, ast.Constant) and isinstance(arg.right.value, int)
            if not (check1 and check2 and check3):
                raise CashflowModelError(msg)

        # The model variable calls something else
        if not (isinstance(arg, ast.Name) or isinstance(arg, ast.Constant) or isinstance(arg, ast.BinOp)):
            raise CashflowModelError(msg)

        # The model variable calls a constant
        if isinstance(arg, ast.Constant):
            if not isinstance(arg.value, int):
                raise CashflowModelError(msg)


def set_calc_direction(variables):
    max_calc_order = variables[-1].calc_order
    for calc_order in range(1, max_calc_order + 1):
        # Multiple variables can have the same calc_order if they are part of the cycle
        calc_order_variables = [v for v in variables if v.calc_order == calc_order]
        calc_direction = get_calc_direction(calc_order_variables)
        for variable in calc_order_variables:
            variable.calc_direction = calc_direction
    return variables
