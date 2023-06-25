import ast
import inspect

from cashflower.cashflow import CashflowModelError


def func_a(t):
    if t > 5:
        if t < 10:
            z = func_b(t)
            return z
    return func_c(t-1)


def func_b(t):
    return t


def func_c(t):
    return func_b(t)


T_MAX = 13


class Dependency:
    def __init__(self, func, call, arg, subset):
        self.func = func
        self.call = call
        self.arg = arg
        self.subset = subset

    def __repr__(self):
        return f"Dependency:\n" \
               f"\tfunc: {self.func}, \n" \
               f"\tcall: {self.call}, \n" \
               f"\targ: {self.arg}, \n" \
               f"\tsubset: {self.subset}"


class Visitor(ast.NodeVisitor):
    """Gather:
    function = func_a
    call = func_b
    arg = t+1
    subset = [0, 10]
    """
    def __init__(self, func):
        self.func = func
        self.dependencies = []

    def visit_Call(self, node):
        arg = get_arg(node, self.func.__name__)
        ifs = get_parent_ifs(node)
        subset = ifs_to_subset(ifs)
        dependency = Dependency(self.func.__name__, node.func.id, arg, subset)
        self.dependencies.append(dependency)


def get_arg(node, name):
    arg = None

    if len(node.args) != 1:
        msg = f"Model variable must have one argument. " \
              f"Please review the call of '{node.func.id}' in the definition of '{name}'."
        raise CashflowModelError(msg)

    # The function has a single argument
    if isinstance(node.args[0], ast.Name):
        arg = node.args[0].id

    # The function has a binary operator as an argument
    if isinstance(node.args[0], ast.BinOp):
        arg = binop_to_arg(node)

    return arg


def get_dependencies(func):
    visitor = Visitor(func)
    code = ast.parse(inspect.getsource(func))
    add_parent(code)
    visitor.visit(code)
    return visitor.dependencies


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


def get_parent_ifs(node):
    """Return list of If nodes which are parents of the node."""
    ifs = []
    current_node = node
    while current_node is not None:
        if isinstance(current_node, ast.If):
            ifs.append(current_node)
        current_node = current_node.parent
    return ifs


def add_parent(root):
    root.parent = None
    for node in ast.walk(root):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return None


def if_to_subset(_if):
    subset = [0, None]

    c1 = _if.test.left.id == "t"
    c2 = len(_if.test.comparators) == 1
    c3 = len(_if.test.ops) == 1

    if c1 and c2 and c3:
        if isinstance(_if.test.comparators[0], ast.Constant):
            value = _if.test.comparators[0].value
            op = _if.test.ops[0]

            if isinstance(op, ast.Eq):
                subset = set(value)

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


def ifs_to_subset(ifs):
    subset = set(range(0, T_MAX))
    for idx, _if in enumerate(ifs):
        if idx == 0:
            subset = if_to_subset(_if)
        else:
            subset = subset & if_to_subset(_if)
    return subset


if __name__ == "__main__":
    func = func_a
    # print(ast.dump(ast.parse(inspect.getsource(func)), indent=2))
    x = get_dependencies(func)
    for el in x:
        print(el)
