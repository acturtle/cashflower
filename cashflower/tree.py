import ast
import inspect


def func_a(x):
    if x == 1:
        z = func_b(x)
        return z
    return func_c(x+1)


def func_b(x):
    return x


def func_c(x):
    return func_b(x)


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.funcs = set()

    def visit_Call(self, node):
        self.funcs.add(node.func.id)


def get_calls(func):
    visitor = Visitor()
    code = ast.parse(inspect.getsource(func))
    visitor.visit(code)
    return visitor.funcs


if __name__ == "__main__":
    result = get_calls(func_c)
    print(result)
    # print(ast.dump(ast.parse(inspect.getsource(func_a)), indent=2))
