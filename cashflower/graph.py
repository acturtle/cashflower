import ast
import inspect

from queue import Queue
from .utils import get_object_by_name




def get_dependencies(func, variable_names, settings):
    visitor = VisitorOld(func, variable_names, settings)
    code = ast.parse(inspect.getsource(func))
    add_parent(code)
    visitor.visit(code)
    return visitor.dependencies


class Dependency:
    def __init__(self, func, call, arg, subset):
        self.func = func
        self.call = call
        self.arg = arg
        self.subset = subset

    def __repr__(self):
        return f"\nDependency:\n" \
               f"\tfunc: {self.func}, \n" \
               f"\tcall: {self.call}, \n" \
               f"\targ: {self.arg}, \n" \
               f"\tsubset: {self.subset}"


class VisitorOld(ast.NodeVisitor):
    def __init__(self, func, variable_names, settings):
        self.func = func
        self.variable_names = variable_names
        self.settings = settings
        self.dependencies = []

    def visit_Call(self, node):
        # raise_error_if_incorrect_argument(node)

        if isinstance(node.func, ast.Name) and node.func.id in self.variable_names:
            # Get function's argument (e.g. None, "t", "t+1", "t-1")
            arg = get_arg(node, self.func.__name__)

            # Get subset of dependency (e.g. all periods or {0, 1, 2, 3})
            # TODO: for now simplified version, find only the nearest If
            # TODO: In the future, find all nested Ifs
            # ifs = get_parent_ifs(node)
            # subset = ifs_to_subset(ifs, self.settings)
            subset = {*range(0, self.settings["T_MAX_CALCULATION"]+1)}
            dependency = Dependency(self.func.__name__, node.func.id, arg, subset)
            self.dependencies.append(dependency)


def get_arg(node, name):
    arg = None

    if len(node.args) != 1:
        msg = f"Model variable must have one argument. " \
              f"Please review the call of '{node.func.id}' in the definition of '{name}'."
        raise ValueError(msg)

    # The function has a single argument
    if isinstance(node.args[0], ast.Name):
        arg = node.args[0].id

    # The function has a binary operator as an argument
    if isinstance(node.args[0], ast.BinOp):
        arg = binop_to_arg(node)

    return arg


def binop_to_arg(node):
    """Currently only fetching t+1 and t-1 arguments."""
    arg = None
    binop = node.args[0]

    c1 = isinstance(binop.left, ast.Name)
    c2 = isinstance(binop.right, ast.Constant)
    c3 = isinstance(binop.op, ast.Add)
    c4 = isinstance(binop.op, ast.Sub)

    if c1 and c2 and c3:
        if binop.right.value == 1:
            arg = "t+1"

    if c1 and c2 and c4:
        if binop.right.value == 1:
            arg = "t-1"

    return arg


def is_child(parent_node, child_node):
    if parent_node == child_node:
        return True

    q = Queue()
    q.put(parent_node)

    while not q.empty():
        node = q.get()
        for subnode in ast.iter_child_nodes(node):
            if subnode == child_node:
                return True
            q.put(subnode)

    return False


def which_if_field(if_node, subnode):
    """To which field of if_node (test/body/orelse) does subnode belong?"""
    test_node = if_node.test
    if is_child(test_node, subnode):
        return "test"

    for body_node in if_node.body:
        if is_child(body_node, subnode):
            return "body"

    for orelse_node in if_node.orelse:
        if is_child(orelse_node, subnode):
            return "orelse"

    return None


def get_parent_ifs(node):
    """Return list of If nodes which are parents of the node."""
    ifs = []
    current_node = node

    while current_node is not None:

        if isinstance(current_node, ast.If):
            ifs.append(current_node)

        child = current_node
        current_node = current_node.parent
        if current_node is not None:
            current_node.child = child

    return ifs


def ifs_to_subset(ifs, settings):
    T_MAX = settings["T_MAX_CALCULATION"]+1
    subset = set(range(0, T_MAX))
    for idx, _if in enumerate(ifs):
        if idx == 0:
            subset = if_to_subset(_if, T_MAX)
        else:
            subset = subset & if_to_subset(_if, T_MAX)
    return subset


def if_to_subset(_if, T_MAX):
    subset = set(range(0, T_MAX))

    if not isinstance(_if.test.left, ast.Name):
        return subset

    c1 = _if.test.left.id == "t"
    c2 = len(_if.test.comparators) == 1
    c3 = len(_if.test.ops) == 1

    if c1 and c2 and c3:
        if isinstance(_if.test.comparators[0], ast.Constant):
            value = _if.test.comparators[0].value
            op = _if.test.ops[0]

            if isinstance(op, ast.Eq):
                subset = {value}

            if isinstance(op, ast.NotEq):
                subset = set([*range(0, value)] + [*range(value+1, T_MAX)])

            if isinstance(op, ast.Lt):
                subset = set(range(0, value))

            if isinstance(op, ast.LtE):
                subset = set(range(0, value+1))

            if isinstance(op, ast.Gt):
                subset = set(range(value+1, T_MAX))

            if isinstance(op, ast.GtE):
                subset = set(range(value, T_MAX))

    return subset


def add_parent(root):
    """Add parent directly to make it easier for analysis."""
    root.parent = None
    for node in ast.walk(root):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return None


def add_edges_from_dependency(dependency, DG, T_MAX):
    if dependency.arg == "t":
        for period in dependency.subset:
            DG.add_edge((dependency.call, period), (dependency.func, period))

    if dependency.arg == "t-1":
        for period in dependency.subset:
            if period - 1 >= 0:
                DG.add_edge((dependency.call, period-1), (dependency.func, period))

    if dependency.arg == "t+1":
        for period in dependency.subset:
            if period + 1 <= T_MAX:
                DG.add_edge((dependency.call, period + 1), (dependency.func, period))

    if dependency.arg is None: #TODO
        for period_1 in range(0, T_MAX):
            for period_2 in range(0, T_MAX):
                DG.add_edge((dependency.call, period_1), (dependency.func, period_2))
    return None
