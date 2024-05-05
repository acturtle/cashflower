import ast
import inspect
import networkx as nx

from collections import deque

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
    """
    Select only variables and nodes that are required by the user.

    This function takes a list of output column names, a list of variables, and a directed graph.
    It filters out the variables and nodes in the graph that are not necessary for the calculation of the output columns.

    Parameters:
        output_columns (list): A list of names of the output columns.
        variables (list): A list of all available variables.
        dg (nx.DiGraph): A directed graph representing the relationships between the variables.

    Returns:
        list: A list of variables that are necessary for the calculation of the output columns.
        nx.DiGraph: A filtered directed graph containing only the necessary nodes and edges.
    """
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
    """
    Returns a list of variables that are called by the given variable.

    Parameters:
        variable (Variable): The variable to check for calls.
        variables (list): A list of all variables.
        argument_t_only (bool): If True, only variables called with "t" will be returned. Defaults to False.

    Returns:
        list: A list of variables that are called by the given variable.

    Notes:
        - If argument_t_only is True, only variables called with "t" will be returned.
          For example, if a variable is called with "t-1", it will not be included in the list.
        - This function uses the ast module to parse the source code of the given variable and find the calls.
        - The function also checks for incorrect arguments and raises an error if found.

    Debug: print("\n", ast.dump(ast_tree, indent=2))
    """
    call_names = []
    variable_names = [variable.name for variable in variables]
    ast_tree = ast.parse(inspect.getsource(variable.func))

    for node in ast.walk(ast_tree):
        # Variable calls other variable directly (e.g. projection_year(t))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in variable_names:
                    raise_error_if_incorrect_argument(node, variable)
                    # Add variable regardless of its argument
                    if argument_t_only is False:
                        call_names.append(node.func.id)
                    # Add variable only if it calls "t"
                    else:
                        if isinstance(node.args[0], ast.Name):
                            call_names.append(node.func.id)

    calls = [get_object_by_name(variables, call_name) for call_name in call_names if call_name != variable.name]
    return calls


def parse_ast_tree(variable, variable_names):
    """
    Parse the Abstract Syntax Tree (AST) of a variable's function and return relevant nodes.

    Args:
        variable: A variable object.
        variable_names: A list of variable names.

    Returns:
        A list of relevant AST nodes.
    """
    ast_tree = ast.parse(inspect.getsource(variable.func))
    relevant_nodes = []
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in variable_names:
                relevant_nodes.append(node)
    return relevant_nodes


def analyze_ast_node(node):
    """
    Analyze an AST node to determine the calculation direction.

    Args:
        node: An AST node.

    Returns:
        A set of calculation directions.
    """
    calc_directions = set()
    for arg in node.args:
        if isinstance(arg, ast.BinOp):
            if isinstance(arg.left, ast.Name) and arg.left.id == "t":
                if isinstance(arg.op, ast.Add):
                    calc_directions.add(-1)
                elif isinstance(arg.op, ast.Sub):
                    calc_directions.add(1)
    return calc_directions


def get_calc_direction(variables):
    """
    Set calculation direction to irrelevant [0] / forward [1] / backward [-1].

    Args:
        variables: A list of variable objects.

    Returns:
        An integer representing the calculation direction.

    Notes:
        "'variables' typically contains a single variable, but in the case of a cycle,
        it may contain multiple variables."
    """
    variable_names = [variable.name for variable in variables]
    calc_directions = set()
    for variable in variables:
        nodes = parse_ast_tree(variable, variable_names)
        for node in nodes:
            calc_directions.update(analyze_ast_node(node))

    # 1 calculation direction
    if len(calc_directions) == 1:
        return list(calc_directions)[0]

    # >1 calculation direction (bidirectional variables are not allowed)
    if len(calc_directions) > 1:
        msg = (f"Bidirectional recursion is not allowed. Please review variables: '{', '.join(variable_names)}'."
               f"\nIf bidirectional recursion is necessary in your project, please raise it on: github.com/acturtle/cashflower")
        raise CashflowModelError(msg)

    return 0


def get_predecessors(node, dg):
    """
    Get the list of all predecessors of a given node in a directed graph.

    Args:
        node: The node for which to get the predecessors.
        dg: The directed graph.

    Returns:
        A list of all nodes that are predecessors of the given node.
    """
    queue = deque([node])
    visited = {node}

    while queue:
        node = queue.popleft()
        for child in dg.predecessors(node):
            if child not in visited:
                queue.append(child)
                visited.add(child)

    return list(visited)


def raise_error_if_incorrect_argument(subnode, variable):
    """
    Raises an error if the argument of a model variable is incorrect.

    Args:
        subnode (ast.AST): The AST node representing the model variable call.
        variable (Variable): The name of the variable being called.

    Raises:
        CashflowModelError: If the argument of the model variable is incorrect.

    Notes:
        Model variables can have maximally two arguments (for time and stochastic scenario).
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

        # The model variable calls a variable [my_variable(t)]
        if isinstance(arg, ast.Name):
            if not arg.id == "t":
                raise CashflowModelError(msg)

        # The model variable calls an operation [my_variable(t+1)]
        if isinstance(arg, ast.BinOp):
            is_valid_name = isinstance(arg.left, ast.Name) and arg.left.id == "t"
            is_valid_operation = isinstance(arg.op, ast.Add) or isinstance(arg.op, ast.Sub)
            is_valid_constant = isinstance(arg.right, ast.Constant) and isinstance(arg.right.value, int)
            if not (is_valid_name and is_valid_operation and is_valid_constant):
                raise CashflowModelError(msg)

        # The model variable calls a constant [my_variable(12)]
        if isinstance(arg, ast.Constant):
            if not isinstance(arg.value, int):
                raise CashflowModelError(msg)

        # The model variable calls something else
        if not (isinstance(arg, ast.Name) or isinstance(arg, ast.Constant) or isinstance(arg, ast.BinOp)):
            raise CashflowModelError(msg)


def set_calc_direction(variables):
    """
    Sets the calculation direction for each variable in the given list.

    Args:
        variables (list): A list of variables for which to set the calculation direction.

    Returns:
        list: The same list of variables with their calculation direction set.
    """
    max_calc_order = variables[-1].calc_order
    for calc_order in range(1, max_calc_order + 1):
        # Multiple variables can have the same calc_order if they are part of the cycle
        calc_order_variables = [v for v in variables if v.calc_order == calc_order]
        calc_direction = get_calc_direction(calc_order_variables)
        for variable in calc_order_variables:
            variable.calc_direction = calc_direction
    return variables
