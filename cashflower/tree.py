import ast
import inspect

from cashflower.cashflow import CashflowModelError


def func_a(t):
    if t == 1:
        z = func_b(t)
        return z
    return func_c(t-1)


def func_b(t):
    return t


def func_c(t):
    return func_b(t)


class Visitor(ast.NodeVisitor):
    def __init__(self, func):
        self.func = func
        self.calls = []

    def visit_Call(self, node):
        arg = None

        if len(node.args) != 1:
            msg = f"Model variable must have one argument. " \
                  f"Please review the call of '{node.func.id}' in the definition of '{self.func.__name__}'."
            raise CashflowModelError(msg)

        # The function has a single argument
        if isinstance(node.args[0], ast.Name):
            arg = node.args[0].id

        # The function has a binary operator as an argument
        if isinstance(node.args[0], ast.BinOp):
            bin_op = node.args[0]

            c1 = isinstance(bin_op.left, ast.Name)
            c2 = isinstance(bin_op.right, ast.Constant)
            c3 = isinstance(bin_op.op, ast.Add)
            c4 = isinstance(bin_op.op, ast.Sub)

            if c1 and c2 and c3:
                if bin_op.right.value == 1:
                    arg = "t+1"

            if c1 and c2 and c4:
                if bin_op.right.value == 1:
                    arg = "t-1"

        self.calls.append((node.func.id, arg))


def get_calls(func):
    visitor = Visitor(func)
    code = ast.parse(inspect.getsource(func))
    visitor.visit(code)
    return visitor.calls


if __name__ == "__main__":
    result = get_calls(func_a)
    print(result)
    # print(ast.dump(ast.parse(inspect.getsource(func_a)), indent=2))
