import copy
import datetime
import functools
import inspect
import os
import time
import pandas as pd
import sys


from . import utils


def assign(var):
    """Assign formula to an object.

    The decorator should be used in the main model script to link variables/parameters and their forulas.
    It also caches the function so that the results get remembered.

    Parameters
    ----------
    var : an object
        Model variable or parameter to which formula is attached.

    Returns
    -------
    decorator
    """
    def wrapper(func):
        func = functools.cache(func)
        var.assigned_formula = func
        return func
    return wrapper


def updt(total, progress):
    """
    Displays or updates a console progress bar.

    Original source: https://stackoverflow.com/a/15860757/1391441
    """
    barLength, status = 20, ""
    progress = float(progress) / float(total)
    if progress >= 1.:
        progress, status = 1, "\r\n"
    block = int(round(barLength * progress))
    text = "\r[{}] {:.0f}% {}".format(
        "#" * block + "-" * (barLength - block), round(progress * 100, 0),
        status)
    sys.stdout.write(text)
    sys.stdout.flush()


class CashflowModelError(Exception):
    pass


class Runplan:
    def __init__(self, data=None, version="1"):
        self.data = data
        self.version = version
        self.set_empty_data()
        self.set_version()
        self.set_index()

    def set_empty_data(self):
        if self.data is None:
            self.data = pd.DataFrame({"version": "1"})

    def set_version(self):
        if "version" not in self.data.columns:
            raise CashflowModelError("Runplan must have the 'version' column.")
        else:
            self.data["version"] = self.data["version"].astype(str)

    def set_index(self):
        self.data = self.data.set_index("version")

    def get(self, attribute):
        return self.data.loc[self.version][attribute]


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
    size : int
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
        self.size = 0
        self.policy_record = None

    def __repr__(self):
        return f"MP: {self.name}"

    def __len__(self):
        return self.data.shape[0]

    def get(self, attribute):
        return self.policy_record[attribute].values[0]

    @property
    def policy_id(self):
        return self._policy_id

    @policy_id.setter
    def policy_id(self, new_policy_id):
        self._policy_id = new_policy_id

        if new_policy_id not in self.data.index:
            raise CashflowModelError(f"There is no policy id '{new_policy_id}' in modelpoint '{self.name}'.")

        self.policy_data = self.data.loc[[new_policy_id]]
        self.size = self.policy_data.shape[0]
        if self.size > 0:
            self.record_num = 0

    @property
    def record_num(self):
        return self._record_num

    @record_num.setter
    def record_num(self, new_record_num):
        self._record_num = new_record_num
        self.policy_record = self.policy_data.iloc[[new_record_num]]


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
    pol_dep : bool
        Should the variable be calculated for each policyholder or only once?
    time_dep : bool
        If true then the variable is independent from time
    assigned_formula : function
        Function attached using the @assign decorator.
    _formula : function
        The formula to calculate the results. It takes definition from assigned_formula.
        While setting, it checks if the formula is recursive.
    recursive : str
        States if the formula is recursive, possible values: 'forward', 'backward' and 'not_recursive'.
    settings : dict
        User settings. Model variable uses T_CALCULATION_MAX setting. Set in get_model_input().
    result : list
        List of n lists with m elements where: n = num of records for policy, m = num of projection months.
    runtime: float
        The runtime of the modelvariable in the model run (in seconds).
    children : list of model variables
        List of model variables that this variable is calling in its formula.
        Only relevant in the model context because model is linked to a group of variables.
    grandchildren : list of model variables
        Children and their descendants (children, grandchildren, grandgrandchildren and so on...).
    """
    instances = []

    def __init__(self, name=None, modelpoint=None, pol_dep=True, time_dep=True):
        self.__class__.instances.append(self)
        self.name = name
        self.modelpoint = modelpoint
        self.pol_dep = pol_dep
        self.time_dep = time_dep
        self.assigned_formula = None
        self._formula = None
        self.recursive = None
        self.settings = None
        self.result = None
        self.runtime = 0
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        if self.name is None:
            return "MV: NoName"
        return f"MV: {self.name}"

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, t=0, r=None):
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        if t < 0 or t > t_calculation_max:
            return 0

        # User might call lower order variable from higher order variable and specify record (r)
        if r is not None:
            return self.result[r][t]

        if self.modelpoint.size == 0:
            return None

        return self.result[self.modelpoint.record_num][t]

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        params = inspect.signature(new_formula).parameters

        if self.time_dep:
            if not (len(params) == 1 and "t" in params.keys()):
                raise CashflowModelError(f"\nModel variable formula must have only one parameter: 't'. "
                                         f"Please check code for '{new_formula.__name__}'.")
        else:
            if not (len(params) == 0):
                raise CashflowModelError(f"\nFormula for time_dep model variable can't have any parameters. "
                                         f"Please check code for '{new_formula.__name__}'.")

        formula_source = inspect.getsource(new_formula)
        clean = utils.clean_formula_source(formula_source)
        self.recursive = utils.is_recursive(clean, self.name)
        self._formula = new_formula

    def clear(self):
        if self.pol_dep:
            self.formula.cache_clear()

    def calculate(self):
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        self.result = [[None] * (t_calculation_max+1) for _ in range(self.modelpoint.size)]

        for r in range(self.modelpoint.size):
            self.modelpoint.record_num = r
            self.clear()

            if self.time_dep:
                if self.recursive == "not_recursive":
                    self.result[r] = list(map(self.formula, range(t_calculation_max+1)))
                elif self.recursive == "backward":
                    for t in range(t_calculation_max, -1, -1):
                        self.result[r][t] = self.formula(t)
                else:
                    for t in range(t_calculation_max+1):
                        self.result[r][t] = self.formula(t)
            else:
                value = self.formula()
                self.result[r] = [value] * (t_calculation_max + 1)


class Parameter:
    def __init__(self, name=None, modelpoint=None):
        self.name = name
        self.modelpoint = modelpoint
        self.assigned_formula = None
        self._formula = None
        self.result = None
        self.runtime = 0
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        if self.name is None:
            return "P: NoName"
        return f"P: {self.name}"

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, r=None):
        # User might call lower order variable from higher order variable and specify record (r)
        if r is not None:
            return self.result[r]

        if self.modelpoint.size == 0:
            return None

        return self.result[self.modelpoint.record_num]

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        params = inspect.signature(new_formula).parameters
        if not (len(params) == 0):
            msg = f"\nFormula can't have any parameters. Please check code for '{new_formula.__name__}'."
            raise CashflowModelError(msg)
        self._formula = new_formula

    def clear(self):
        self.formula.cache_clear()

    def calculate(self):
        self.result = [None] * self.modelpoint.size
        for r in range(self.modelpoint.size):
            self.modelpoint.record_num = r
            self.clear()
            self.result[r] = self.formula()


class Model:
    """Actuarial cash flow model.

    Model combines variables and modelpoints. Variables are ordered into a calculation queue.
    All variables are calculated for data of each policyholder in the modelpoints.

    Attributes
    ----------
    name : str
        Model's name
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
    def __init__(self, name, variables, parameters, modelpoints, settings):
        self.name = name
        self.variables = variables
        self.parameters = parameters
        self.modelpoints = modelpoints
        self.settings = settings
        self.components = variables + parameters
        self.queue = []
        self.empty_output = None
        self.output = None

    def get_component_by_name(self, name):
        for component in self.components:
            if component.name == name:
                return component

    def get_variable_by_name(self, name):
        for variable in self.variables:
            if variable.name == name:
                return variable

    def get_modelpoint_by_name(self, name):
        for modelpoint in self.modelpoints:
            if modelpoint.name == name:
                return modelpoint

    def set_children(self):
        component_names = [component.name for component in self.components]
        for component in self.components:
            formula_source = inspect.getsource(component.formula)
            cleaned_formula_source = utils.clean_formula_source(formula_source)
            child_names = utils.list_called_funcs(cleaned_formula_source, component_names)

            # Return objects instead of names
            for child_name in child_names:
                if child_name != component.name:
                    child = self.get_component_by_name(child_name)
                    component.children.append(child)

    def set_grandchildren(self):
        for component in self.components:
            component.grandchildren = list(component.children)
            i = 0
            while i < len(component.grandchildren):
                grandchild = component.grandchildren[i]
                component.grandchildren = utils.unique_extend(component.grandchildren, grandchild.children)
                i += 1

    def remove_from_grandchildren(self, removed_component):
        for component in self.components:
            if removed_component in component.grandchildren:
                component.grandchildren.remove(removed_component)

    def set_queue(self):
        queue = []
        components = sorted(self.components)
        while components:
            component = components[0]
            queue.append(component)
            self.remove_from_grandchildren(component)
            components.remove(component)
            components = sorted(components)
        self.queue = queue

    def set_empty_output(self):
        empty_output = dict()
        aggregate = self.settings["AGGREGATE"]

        # Each modelpoint has a separate output file
        for modelpoint in self.modelpoints:
            empty_output[modelpoint.name] = pd.DataFrame()
            empty_output[modelpoint.name]["t"] = None
            # Individual output contains record numbers
            if not aggregate:
                empty_output[modelpoint.name]["r"] = None

        # Aggregated output contains only variables, individual outputs contains variables and parameters
        if aggregate:
            for variable in self.variables:
                empty_output[variable.modelpoint.name][variable.name] = None
        else:
            for component in self.components:
                empty_output[component.modelpoint.name][component.name] = None

        self.empty_output = empty_output

    def clear_components(self):
        for component in self.components:
            component.clear()

    def calculate_one_policy(self):
        policy_output = copy.deepcopy(self.empty_output)
        aggregate = self.settings["AGGREGATE"]
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], t_calculation_max)

        for c in self.queue:
            start = time.time()
            try:
                c.calculate()
                # Variables are always in the output
                if isinstance(c, ModelVariable):
                    if c.modelpoint.size == 1:
                        policy_output[c.modelpoint.name][c.name] = c.result[0][:t_output_max+1]
                    elif aggregate:
                        policy_output[c.modelpoint.name][c.name] = utils.aggregate(c.result, t_output_max+1)
                    else:
                        policy_output[c.modelpoint.name][c.name] = utils.flatten(c.result, t_output_max+1)
                # Parameters are added only to individual output
                if isinstance(c, Parameter) and not aggregate:
                    if c.modelpoint.size == 1:
                        policy_output[c.modelpoint.name][c.name] = c.result * (t_output_max+1)
                    else:
                        policy_output[c.modelpoint.name][c.name] = [r for r in c.result for _ in range(t_output_max+1)]
            except:
                raise CashflowModelError(f"Unable to evaluate '{c.name}'.")
            end = time.time()
            c.runtime += end - start

        # Add time and record number to the individual output
        if not aggregate:
            for modelpoint in self.modelpoints:
                policy_output[modelpoint.name]["t"] = list(range(t_output_max+1)) * modelpoint.size
                policy_output[modelpoint.name]["r"] = utils.repeated_numbers(modelpoint.size, t_output_max+1)

        return policy_output

    def calculate_all_policies(self):
        output = copy.deepcopy(self.empty_output)
        aggregate = self.settings["AGGREGATE"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], self.settings["T_CALCULATION_MAX"])
        primary = self.get_modelpoint_by_name("policy")

        n_pols = len(primary)
        utils.print_log(f"Number of policies: {n_pols}")

        policy_outputs = []
        for row in range(n_pols):
            policy_id = primary.data.index[row]

            for m in self.modelpoints:
                m.policy_id = policy_id

            self.clear_components()
            policy_output = self.calculate_one_policy()
            policy_outputs.append(policy_output)
            updt(n_pols, row + 1)

        utils.print_log("Preparing results")
        for m in self.modelpoints:
            if aggregate:
                output[m.name] = sum(policy_output[m.name] for policy_output in policy_outputs)
                output[m.name]["t"] = list(range(t_output_max+1))
            else:
                output[m.name] = pd.concat(policy_output[m.name] for policy_output in policy_outputs)

        self.output = output

    def run(self):
        start = time.time()
        utils.print_log(f"Start run for model '{self.name}'")
        output_columns = self.settings["OUTPUT_COLUMNS"]
        user_chose_columns = len(output_columns) > 0
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.set_empty_output()
        self.set_children()
        self.set_grandchildren()
        self.set_queue()
        self.calculate_all_policies()

        if not os.path.exists("output"):
            os.makedirs("output")

        utils.print_log("Saving files:")
        for modelpoint in self.modelpoints:
            filepath = f"output/{timestamp}_{modelpoint.name}.csv"
            print(f"{' '*10} {filepath}")

            mp_output = self.output.get(modelpoint.name)
            if user_chose_columns:
                output_columns.extend(["t", "r"])
                columns = mp_output.columns.intersection(output_columns)
                mp_output.to_csv(filepath, index=False, columns=columns)
            else:
                mp_output.to_csv(filepath, index=False)

        # Save runtime
        if self.settings["SAVE_RUNTIME"]:
            data = [(c.name, c.runtime) for c in self.components]
            runtime = pd.DataFrame(data, columns=["component", "runtime"])
            runtime.to_csv(f"output/{timestamp}_runtime.csv", index=False)
            print(f"{' '*10} output/{timestamp}_runtime.csv")

        end = time.time()
        utils.print_log(f"Finished. Elapsed time: {round(end-start, 2)} seconds.")
