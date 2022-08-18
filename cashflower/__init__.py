import datetime
import functools
import inspect
import os
import pandas as pd

from . import admin
from . import utils


def assign(var):
    """Assign formula to a model variable.

    The decorator should be used in the main model script to link model variables and their forulas.
    It also caches the function so that the results get remembered.

    Parameters
    ----------
    var : model variable object
        Model variable to which formula is attached.

    Returns
    -------
    decorator
    """
    def wrapper(func):
        func = functools.cache(func)
        var.formula = func
        return func
    return wrapper


def get_model_input(modelpoint_module, model_module, settings):
    """Prepare input for model.

    Gathers all model points and model variable instances.
    Assigns names to model variables and, if not assigned by user, also model points.
    (User doesn't have to assign a model point to a model variable if there is only one model point.)

    Parameters
    ----------
    modelpoint_module : module
        Module where user defines model points.
    model_module : module
        Module where user defines model variables.
    settings : dict
        Dictionary with user settings.

    Returns
    -------
    tuple
        Contains two lists - model variables and model points.
    """

    # Gather model points
    modelpoint_members = inspect.getmembers(modelpoint_module)
    modelpoint_members = [m for m in modelpoint_members if isinstance(m[1], ModelPoint)]

    modelpoints = []
    for name, modelpoint in modelpoint_members:
        modelpoint.name = name
        modelpoint.settings = settings
        modelpoints.append(modelpoint)

    first_modelpoint = modelpoints[0]

    # Gather model variables
    model_members = inspect.getmembers(model_module)
    model_members = [m for m in model_members if isinstance(m[1], ModelVariable)]

    variables = []
    for name, variable in model_members:
        variable.name = name
        variable.settings = settings
        if variable.modelpoint is None:
            variable.modelpoint = first_modelpoint
        variables.append(variable)

    return variables, modelpoints


def load_settings(settings):
    """Load model settings.

    The function firstly reads the default settings and then overwrites these that have been defined by the user.
    The function helps with backward compatibility.
    If there is a new setting in the package, the user doesn't have to have it in the settings script.

    Parameters
    ----------
    settings : dict
        Model settings defined by the user.

    Returns
    -------
    dict
        Full set of settings.
    """
    initial_settings = {
        "POLICY_ID_COLUMN": "POLICY_ID",
        "T_CALCULATION_MAX": 1440,
        "T_OUTPUT_MAX": 1440,
        "AGGREGATE": False,
        "OUTPUT_COLUMNS": [],
    }

    for key, value in settings.items():
        initial_settings[key] = value

    return initial_settings


class ModelPoint:
    """Policyholders' data.

    The model point stores data on all policyholders and points to a specific policyholder
    for which model should be calculated.

    Attributes
    ----------
    data : data frame
        Policyholders' data.
    name : str
        Used in the output filename. Set in get_model_input().
    settings : dict
        User settings. Model point uses POLICY_ID_COLUMN setting. Set in get_model_input().
    _policy_id : str
        Value to identify the policyholder by in the column defined by POLICY_ID_COLUMN setting.
        Looped over in model.calculated_all_policies().
    _record_num : int
        Number of records - relevant when there are multiple records for the same policyholder.
        Looped over in model_variable.calculate().
    policy_data : data frame
        Row(s) of data for the current policyholder.
    policy_nrow : int
        Number of rows of policy data.
    policy_record : data frame
        Row of data for the current policyholder and record.
    """

    instances = []

    def __init__(self, data):
        self.__class__.instances.append(self)
        self.data = data
        self.name = None
        self.settings = None
        self._policy_id = None
        self._record_num = None
        self.policy_data = None
        self.policy_nrow = 0
        self.policy_record = None

    def __repr__(self):
        return f"MP: {self.name}"

    def __len__(self):
        return self.data.shape[0]

    def get(self, attribute):
        return self.policy_record[attribute]

    @property
    def policy_id(self):
        return self._policy_id

    @policy_id.setter
    def policy_id(self, new_policy_id):
        policy_id_column = self.settings["POLICY_ID_COLUMN"]
        self._policy_id = new_policy_id
        self.policy_data = self.data[self.data[policy_id_column] == new_policy_id]
        self.policy_nrow = self.policy_data.shape[0]

    @property
    def record_num(self):
        return self._record_num

    @record_num.setter
    def record_num(self, new_record_num):
        self._record_num = new_record_num
        self.policy_record = self.policy_data.iloc[new_record_num]


class ModelVariable:
    """Variable of a cash flow model.

    Model variable is linked to a modelpoint and calculates results based on the formula.

    Attributes
    ----------
    name : str
        Name of the code variable which is set in get_model_input().
    modelpoint : ModelPoint object
        Model point to which the variable is linked.
        User sets it directly in the model script, otherwise it is set to the first modelpoint in get_model_input().
    recalc : bool
        Should the variable be calculated for each policyholder or only once?
    formula : function
        The formula to calculate the results. It is attached using the @assign decorator.
    settings : dict
        User settings. Model variable uses T_CALCULATION_MAX setting. Set in get_model_input().
    result : list
        List of n lists with m elements where: n = num of records for policy, m = num of projection months.
    children : list of model variables
        List of model variables that this variable is calling in its formula.
        Only relevant in the model context because model is linked to a group of variables.
    grandchildren : list of model variables
        Children and their descendants (children, grandchildren, grandgrandchildren and so on...).
    """
    instances = []

    def __init__(self, name=None, modelpoint=None, recalc=True):
        self.__class__.instances.append(self)
        self.name = name
        self.modelpoint = modelpoint
        self.recalc = recalc
        self.formula = None
        self.settings = None
        self.result = None
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        return f"MV: {self.name}"

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, t, r=None):
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        if t < 0 or t > t_calculation_max:
            return 0

        # User might call lower order variable from higher order variable and specify record (r)
        if r is not None:
            return self.result[r][t]

        return self.formula(t)

    def clear(self):
        if self.recalc:
            self.formula.cache_clear()

    def calculate(self):
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        self.result = [None] * self.modelpoint.policy_nrow

        for r in range(self.modelpoint.policy_nrow):
            self.modelpoint.record_num = r
            self.clear()

            # The try-except formula helps with autorecursive functions
            try:
                self.result[r] = list(map(self.formula, range(t_calculation_max+1)))
            except RecursionError:
                lst = list(map(self.formula, range(t_calculation_max, -1, -1)))
                lst.reverse()
                self.result[r] = lst


class Model:
    """Actuarial cash flow model.

    Model combines variables and modelpoints. Variables are ordered into a calculation queue.
    All variables are calculated for data of each policyholder in the modelpoints.

    Attributes
    ----------
    variables : list
        List of model variables objects.
    modelpoints : list
        List of model point objects.
    settings : dict
        User settings.
    queue : list
        List of model variables in an order in which they should be calculated.
    empty_output : dict
        Empty dict with keys prepared for output
    output : dict
        Dict with key = modelpoints, values = data frames (columns for model variables).
    """
    def __init__(self, variables, modelpoints, settings):
        self.variables = variables
        self.modelpoints = modelpoints
        self.settings = settings
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
            child_names = utils.list_used_words(formula_source, variable_names)
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
        aggregate = self.settings["AGGREGATE"]

        for modelpoint in self.modelpoints:
            empty_output[modelpoint.name] = pd.DataFrame()
            empty_output[modelpoint.name]["t"] = None
            if not aggregate:
                empty_output[modelpoint.name]["r"] = None

        for variable in self.variables:
            empty_output[variable.modelpoint.name][variable.name] = None

        self.empty_output = empty_output


    def clear_variables(self):
        for variable in self.variables:
            variable.clear()

    def calculate_one_policy(self):
        policy_output = self.empty_output.copy()
        aggregate = self.settings["AGGREGATE"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], self.settings["T_CALCULATION_MAX"])

        for var in self.queue:
            var.calculate()
            if aggregate:
                policy_output[var.modelpoint.name][var.name] = utils.aggregate(var.result, n=t_output_max + 1)
            else:
                policy_output[var.modelpoint.name][var.name] = utils.flatten(var.result, n=t_output_max + 1)

        if not aggregate:
            for modelpoint in self.modelpoints:
                policy_output[modelpoint.name]["t"] = list(range(t_output_max + 1)) * modelpoint.policy_nrow
                policy_output[modelpoint.name]["r"] = utils.repeated_numbers(modelpoint.policy_nrow, t_output_max + 1)

        return policy_output

    def calculate_all_policies(self):
        output = self.empty_output.copy()
        aggregate = self.settings["AGGREGATE"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], self.settings["T_CALCULATION_MAX"])
        policy_id_column = self.settings["POLICY_ID_COLUMN"]
        primary = self.get_modelpoint("policy")

        policy_outputs = []
        for row in range(len(primary)):
            policy_id = primary.data.iloc[row][policy_id_column]

            for modelpoint in self.modelpoints:
                modelpoint.policy_id = policy_id

            self.clear_variables()
            policy_output = self.calculate_one_policy()
            policy_outputs.append(policy_output)

        for modelpoint in self.modelpoints:
            if aggregate:
                output[modelpoint.name]["t"] = list(range(t_output_max+1))
                output[modelpoint.name] = sum(policy_output[modelpoint.name] for policy_output in policy_outputs)
            else:
                output[modelpoint.name] = pd.concat(policy_output[modelpoint.name] for policy_output in policy_outputs)

        self.output = output

    def run(self):
        output_columns = self.settings["OUTPUT_COLUMNS"]
        user_chose_columns = len(output_columns) > 0
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.set_empty_output()
        self.set_children()
        self.set_grandchildren()
        self.set_queue()
        self.calculate_all_policies()

        if not os.path.exists("mp_output"):
            os.makedirs("mp_output")

        for modelpoint in self.modelpoints:
            filepath = f"mp_output/{timestamp}_{modelpoint.name}.csv"

            mp_output = self.output.get(modelpoint.name)
            if user_chose_columns:
                output_columns.extend(["t", "r"])
                columns = mp_output.columns.intersection(output_columns)
                mp_output.to_csv(filepath, index=False, columns=columns)
            else:
                mp_output.to_csv(filepath, index=False)
