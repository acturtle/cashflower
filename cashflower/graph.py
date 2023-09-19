import ast
import inspect

from queue import Queue

from .error import CashflowModelError
from .utils import get_object_by_name


def get_calls(variable, variables):
    """List variables called by the given variable"""
    call_names = []
    variable_names = [variable.name for variable in variables]
    node = ast.parse(inspect.getsource(variable.func))

    # Print ast tree (debug)
    # print("\n", ast.dump(node, indent=2))

    for subnode in ast.walk(node):
        # Variable calls other variable directly (e.g. projection_year(t))
        if isinstance(subnode, ast.Call):
            if isinstance(subnode.func, ast.Name):
                if subnode.func.id in variable_names:
                    raise_error_if_incorrect_argument(subnode)
                    call_names.append(subnode.func.id)

    calls = [get_object_by_name(variables, call_name) for call_name in call_names if call_name != variable.name]
    return calls


def get_calc_direction(variables):
    """Set calculation direction to irrelevant [0] / forward [1] / backward [-1]"""
    # For non-cycle => single variable, for cycle => variables from the cycle
    variable_names = [variable.name for variable in variables]

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
                                return -1

                            if check1 and check3:
                                return 1

    return 0


def get_predecessors(node, DG):
    """Get list of predecessors and their predecessors and their..."""
    queue = Queue()
    visited = []

    queue.put(node)
    visited.append(node)

    while not queue.empty():
        node = queue.get()
        for child in DG.predecessors(node):
            if child not in visited:
                queue.put(child)
                visited.append(child)

    return visited


def raise_error_if_incorrect_argument(node):
    # More than 1 argument
    if len(node.args) > 1:
        msg = f"Model variable must have maximally one argument. Please review the call of '{node.func.id}'."
        raise CashflowModelError(msg)

    # Exactly 1 argument
    if len(node.args) == 1:
        # Model variable can only call t, t+/-x, and x
        arg = node.args[0]
        msg = f"\nPlease review '{node.func.id}'. The argument of a model variable can be only:\n" \
              f"- t,\n" \
              f"- t plus/minus integer (e.g. t+1 or t-12),\n" \
              f"- an integer (e.g. 0 or 12)."

        # The model variable calls a variable
        if isinstance(arg, ast.Name):
            if not arg.id == "t":
                raise CashflowModelError(msg)

        # The model variable calls a constant
        if isinstance(arg, ast.Constant):
            if not isinstance(arg.value, int):
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
