import pandas as pd
import inspect

from .utils import list_used_words, unique_extend


class ModelPoint:
    def __init__(self, data, record_num=0):
        self.data = data
        self.record_num = record_num

    def __len__(self):
        return self.data.shape[0]

    def get(self, attribute):
        return self.data.iloc[self.record_num][attribute]

    def set_record_num(self, value):
        self.record_num = value


class ModelVariable:
    instances = []

    def __init__(self, name):
        self.__class__.instances.append(self)
        self.name = name
        self.formula = None
        self.result = [None] * 1440
        self.children = []
        self.grandchildren = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __call__(self, t):
        if t < 0 or t >= 1440:
            return 0
        elif self.result[t] is None:
            self.result[t] = self.formula(t)
        return self.result[t]

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def calculate(self):
        try:
            for t in range(1440):
                self.result[t] = self(t)
        except RecursionError:
            for t in range(1440-1, -1, -1):
                self.result[t] = self(t)


class Model:
    def __init__(self, model_point, variables):
        self.model_point = model_point
        self.variables = variables
        self.output = None

    def get_variable(self, name):
        for variable in self.variables:
            if variable.name == name:
                return variable

    def set_children(self):
        variable_names = [variable.name for variable in self.variables]
        for variable in self.variables:
            formula_source = inspect.getsource(variable.formula)
            child_names = list_used_words(formula_source, variable_names)  # TODO too primitive and error-prone
            for child_name in child_names:
                if child_name != variable.name:
                    child = self.get_variable(child_name)
                    variable.children.append(child)

    def set_grandchildren(self):
        for variable in self.variables:
            variable.grandchildren = list(variable.children)
            for grandchild in variable.grandchildren:
                variable.grandchildren = unique_extend(variable.grandchildren, grandchild.children)

    def sort(self):
        self.variables = sorted(self.variables)

    def remove_from_grandchildren(self, removed_variable):
        for variable in self.variables:
            if removed_variable in variable.grandchildren:
                variable.grandchildren.remove(removed_variable)

    def calculate(self):
        self.sort()
        for variable in self.variables:
            variable.calculate()
            self.remove_from_grandchildren(variable)
            self.sort()

    def set_output(self):
        output = pd.DataFrame()
        for variable in self.variables:
            output[variable.name] = variable.result
        self.output = output
