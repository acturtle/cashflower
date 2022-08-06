import datetime
import inspect
import os
import pandas as pd

from . import admin
from . import utils


def assign(var):
    def wrapper(func):
        var.formula = func
        return func
    return wrapper


class ModelPoint:
    instances = []

    def __init__(self, name, data):
        self.__class__.instances.append(self)
        self.name = name
        self.data = data
        self.policy_id = 1
        self.record_num = 0
        self.size = self.data[self.data["POLICY_ID"] == self.policy_id].shape[0]

    def __repr__(self):
        return self.name

    def __len__(self):
        return self.data.shape[0]

    def get(self, attribute, r=None):
        if r is None:
            r = self.record_num
        df = self.data
        df = df[df["POLICY_ID"] == self.policy_id]
        return df.iloc[r][attribute]


class ModelVariable:
    instances = []

    def __init__(self, name=None, modelpoint=None):
        self.__class__.instances.append(self)
        self.name = name
        self._modelpoint = modelpoint
        self.result = [[None] * 1440 for _ in range(modelpoint.size)] if modelpoint else None
        self.formula = None
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, t, r=None):
        if r is None:
            r = self.modelpoint.record_num
        if t < 0 or t >= 1440:
            return 0
        elif self.result[r][t] is None:
            self.result[r][t] = self.formula(t)
        return self.result[r][t]

    @property
    def modelpoint(self):
        return self._modelpoint

    @modelpoint.setter
    def modelpoint(self, new_modelpoint):
        self._modelpoint = new_modelpoint
        self.result = [[None] * 1440 for _ in range(new_modelpoint.size)]

    def calculate(self):
        for r in range(self.modelpoint.size):
            self.modelpoint.record_num = r
            # The try-except formula helps with autorecursive functions
            try:
                for t in range(1440):
                    self.result[r][t] = self(t, r)
            except RecursionError:
                for t in range(1440-1, -1, -1):
                    self.result[r][t] = self(t, r)


class Model:
    def __init__(self, variables):
        self.variables = variables
        self.queue = []
        self.output = None

    def get_variable(self, name):
        for variable in self.variables:
            if variable.name == name:
                return variable

    def set_children(self):
        variable_names = [variable.name for variable in self.variables]
        for variable in self.variables:
            formula_source = inspect.getsource(variable.formula)
            child_names = utils.list_used_words(formula_source, variable_names)  # TODO
            for child_name in child_names:
                if child_name != variable.name:
                    child = self.get_variable(child_name)
                    variable.children.append(child)

    def set_grandchildren(self):
        for variable in self.variables:
            variable.grandchildren = list(variable.children)
            for grandchild in variable.grandchildren:
                variable.grandchildren = utils.unique_extend(variable.grandchildren, grandchild.children)

    def remove_from_grandchildren(self, removed_variable):
        for variable in self.variables:
            if removed_variable in variable.grandchildren:
                variable.grandchildren.remove(removed_variable)

    def set_queue(self):
        queue = []
        variables = sorted(self.variables)
        while variables:
            variable = variables[0]
            queue.append(variable)
            self.remove_from_grandchildren(variable)
            variables.remove(variable)
            variables = sorted(variables)
        self.queue = queue

    def calculate(self):
        output = dict()

        for variable in self.queue:
            variable.calculate()

            # First variable for the given modelpoint
            if output.get(variable.modelpoint.name) is None:
                output[variable.modelpoint.name] = pd.DataFrame()
                output[variable.modelpoint.name]["t"] = list(range(1440)) * variable.modelpoint.size

                # Multiple records in the modelpoint
                if variable.modelpoint.size > 1:
                    output[variable.modelpoint.name]["r"] = utils.repeated_numbers(2, 1440)

            for r in range(variable.modelpoint.size):
                output[variable.modelpoint.name][variable.name] = utils.flatten(variable.result)

        self.output = output

    def run(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.set_children()
        self.set_grandchildren()
        self.set_queue()
        self.calculate()

        if not os.path.exists("output"):
            os.makedirs("output")

        for mp in ModelPoint.instances:
            filepath = f"output/{timestamp}_{mp.name}.csv"
            self.output.get(mp.name).to_csv(filepath)
