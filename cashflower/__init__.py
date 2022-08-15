import time

import datetime
import functools
import inspect
import os
import pandas as pd

from . import admin
from . import utils


def assign(var):
    def wrapper(func):
        func = functools.cache(func)
        var.formula = func
        return func
    return wrapper


def get_model_input(modelpoint_module, model_module):
    modelpoint_members = inspect.getmembers(modelpoint_module)
    modelpoints = [m[1] for m in modelpoint_members if isinstance(m[1], ModelPoint)]
    first_modelpoint = modelpoints[0]

    model_members = inspect.getmembers(model_module)
    model_members = [m for m in model_members if isinstance(m[1], ModelVariable)]

    variables = []
    for name, variable in model_members:
        variable.name = name
        if variable.modelpoint is None:
            variable.modelpoint = first_modelpoint
        variables.append(variable)

    return variables, modelpoints


class ModelPoint:
    """Model Point class

    data = data frame with data for all policies
    policy_id = id for the current policy that is being calculated
    record_num = if the given policy has multiple records, which record is currently used
    size = how many records the curreny policy have (>=1)
    policy_data = data frame with rows only for the current policy_id
    policy_record = row of data frame for the current policy_id and record_num
    """

    instances = []

    def __init__(self, name, data):
        self.__class__.instances.append(self)
        self.name = name
        self.data = data
        self._policy_id = None
        self._record_num = None
        self.size = 0
        self.policy_data = None
        self.policy_record = None

    def __repr__(self):
        return f"MP: {self.name}"

    def __len__(self):
        return self.data.shape[0]

    @functools.cache
    def get(self, attribute):
        return self.policy_record[attribute]

    @property
    def policy_id(self):
        return self._policy_id

    @policy_id.setter
    def policy_id(self, new_policy_id):
        """ Policy id in model point is changed by model.calculated_all_policies() """
        self._policy_id = new_policy_id
        self.policy_data = self.data[self.data["POLICY_ID"] == new_policy_id]
        self.size = self.policy_data.shape[0]

    @property
    def record_num(self):
        return self._record_num

    @record_num.setter
    def record_num(self, new_record_num):
        """ Record number is changed in model_variable.calculate() """
        self._record_num = new_record_num
        self.policy_record = self.policy_data.iloc[new_record_num]
        self.get.cache_clear()


class ModelVariable:
    """ Model Variable class

    name = it is set to code variable name is get_model_input()
    modelpoint = user sets it directly; otherwise it is set to the first modelpoint in get_model_input()
    recalc = should be recalculated for each policyholder or calculate only once
    formula = function of the variable, attached with @assign
    result = initially None, then list of n lists with m elements where:
        n = num of records for policy, m = num of projection months
    children = only relevant in model context (because then we know the groups of variables),
        which variables is this function calling?
    grandchildren = children and their descendants (i.e. also grandgrandchildren and so on)
    """
    instances = []

    def __init__(self, name=None, modelpoint=None, recalc=True):
        self.__class__.instances.append(self)
        self.name = name
        self.modelpoint = modelpoint
        self.recalc = recalc
        self.formula = None
        self.result = None
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        return f"MV: {self.name}"

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, t, r=None):
        if t < 0 or t >= 1440:
            return 0

        # User calls lower order variable from higher order variable
        if r is not None:
            return self.result[r][t]

        return self.formula(t)

    def calculate(self):
        self.result = [[None] * 1440 for _ in range(self.modelpoint.size)]

        for r in range(self.modelpoint.size):
            self.modelpoint.record_num = r
            self.clear()

            # The try-except formula helps with autorecursive functions
            try:
                self.result[r] = list(map(self.formula, range(1440)))
            except RecursionError:
                self.result[r] = list(map(self.formula, range(1440-1, -1, -1)))

    def clear(self):
        if self.recalc:
            self.formula.cache_clear()


class Model:
    """Model class

     A model is a set of variables and a set of modelpoints.

     variables = list of model variable objects
     modelpoints = list of model point objects
     queue = in which order should variables be calculated?
     output = dict with key=modelpoints, values=data frames with column names are variable names

     """
    def __init__(self, variables, modelpoints):
        self.variables = variables
        self.modelpoints = modelpoints
        self.queue = []
        self.empty_output = None
        self.output = None

    def get_variable(self, name):
        for variable in self.variables:
            if variable.name == name:
                return variable

    def get_modelpoint(self, name):
        for modelpoint in self.modelpoints:
            if modelpoint.name == name:
                return modelpoint

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

    def set_empty_output(self):
        empty_output = dict()
        for modelpoint in self.modelpoints:
            empty_output[modelpoint.name] = pd.DataFrame()

        for variable in self.variables:
            empty_output[variable.modelpoint.name][variable.name] = None
        self.empty_output = empty_output

    def get_empty_output(self):
        empty_output = dict()
        for modelpoint in self.modelpoints:
            empty_output[modelpoint.name] = pd.DataFrame()

        for variable in self.variables:
            empty_output[variable.modelpoint.name][variable.name] = None
        return empty_output

    def clear_variables(self):
        for variable in self.variables:
            variable.clear()

    def calculate_one_policy(self):
        output = self.get_empty_output()

        # variable.result is a list of lists
        for variable in self.queue:
            variable.calculate()
            output[variable.modelpoint.name][variable.name] = utils.flatten(variable.result)

        # output contains time and record number
        for modelpoint in self.modelpoints:
            output[modelpoint.name]["t"] = list(range(1440)) * modelpoint.size
            output[modelpoint.name]["r"] = utils.repeated_numbers(modelpoint.size, 1440)

        return output

    def calculate_all_policies(self):
        output = self.get_empty_output()
        primary = self.get_modelpoint("policy")

        for row in range(len(primary)):
            start = time.time()

            # Primary modelpoint has unique column with policy ID
            policy_id = primary.data.iloc[row]["POLICY_ID"]

            # All modelpoints must have the same policy ID
            for modelpoint in self.modelpoints:
                modelpoint.policy_id = policy_id

            self.clear_variables()
            policy_output = self.calculate_one_policy()

            for modelpoint in self.modelpoints:
                output[modelpoint.name] = pd.concat([output[modelpoint.name], policy_output[modelpoint.name]])

        self.output = output

    def run(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.set_empty_output()
        self.set_children()
        self.set_grandchildren()
        self.set_queue()
        self.calculate_all_policies()

        if not os.path.exists("output"):
            os.makedirs("output")

        for mp in ModelPoint.instances:
            filepath = f"output/{timestamp}_{mp.name}.csv"
            self.output.get(mp.name).to_csv(filepath)

