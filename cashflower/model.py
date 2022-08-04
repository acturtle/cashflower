import pandas as pd
import inspect

from .utils import list_used_words, unique_extend


class ModelPoint:
    def __init__(self, data):
        self.data = data
        self.name = None
        self.policy_id = 1
        self.record_num = 0
        self.size = self.data[self.data["POLICY_ID"] == self.policy_id].shape[0]

    def __len__(self):
        return self.data.shape[0]

    # def __str__(self):
    #     return "MP: " + self.name
    #
    # def __repr__(self):
    #     return "MP: " + self.name

    def get(self, attribute):
        # TODO we are unnecessarily filtering data each time when we want to get a value
        # TODO perhaps better to go policy by policy and only retrieve specific column
        # print("attribute:", attribute)
        # if record_num is None:
        #     record_num = self.record_num
        # print("record num =", self.record_num)
        df = self.data
        df = df[df["POLICY_ID"] == self.policy_id]
        return df.iloc[self.record_num][attribute]


class ModelVariable:
    instances = []

    def __init__(self):
        self.__class__.instances.append(self)
        self.name = None
        self.submodel = None
        self.formula = None
        self.result = None
        self._modelpoint = None
        self.children = []
        self.grandchildren = []

    def __str__(self):
        return "MV: " + self.name

    def __repr__(self):
        return "MV: " + self.name

    def __call__(self, t):
        r = self.modelpoint.record_num

        # print("\nr=", r)
        # print("t=", t)
        # print("result=", self.result[r][t])
        # print("call", self.modelpoint)

        if t < 0 or t >= 13:
            return 0
        elif self.result[r][t] is None:
            self.result[r][t] = self.formula(t)
        return self.result[r][t]

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    @property
    def modelpoint(self):
        return self._modelpoint

    @modelpoint.setter
    def modelpoint(self, new_modelpoint):
        self._modelpoint = new_modelpoint
        self.result = [[None] * 13 for _ in range(new_modelpoint.size)]

    def calculate(self):
        for r in range(self.modelpoint.size):
            # print("\n")
            # print("mp =", self.modelpoint)
            # print("r =", r)
            self.modelpoint.record_num = r
            # print("self.modelpoint.record_num =", self.modelpoint.record_num)
            # The try-except formula helps with autorecursive functions
            try:
                for t in range(13):
                    self.result[r][t] = self(t)
            except RecursionError:
                for t in range(13-1, -1, -1):
                    self.result[r][t] = self(t)


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
        output = pd.DataFrame()
        for variable in self.queue:
            variable.calculate()
            print(variable.name)
            print(variable.result)
            output[variable.name] = variable.result[0]  # TODO
        self.output = output

    def run(self):
        # calculate
        # add/concatenate output to overall output
        # clear results
        # move mmdel point
        pass
