import copy
import datetime
import functools
import inspect
import numpy as np
import os
import time
import pandas as pd
import sys


from . import utils


def assign(var):
    """Assign formula to an object.
    
    The decorator links model components and their formulas.
    The decorator also caches the function so that the results get remembered.

    Parameters
    ----------
    var : an object
        Model component to which formula is attached.
    """
    def wrapper(func):
        func = functools.cache(func)
        var.assigned_formula = func
        return func
    return wrapper


def updt(total, progress):
    """Display or update a console progress bar.
    Original source: https://stackoverflow.com/a/15860757/1391441
    """
    bar_length, status = 20, ""
    progress = float(progress) / float(total)
    if progress >= 1.:
        progress, status = 1, "\r\n"
    block = int(round(bar_length * progress))
    text = "\r[{}] {:.0f}% {}".format(
        "#" * block + "-" * (bar_length - block), round(progress * 100, 0),
        status)
    sys.stdout.write(text)
    sys.stdout.flush()


class CashflowModelError(Exception):
    pass


class Runplan:
    """Runplan of the cash flow model.

    Attributes
    ----------
    data : data frame
        Data for runplan which must contain column named 'version'.
    _version : str
        Current version to be evaluated.
    """
    def __init__(self, data=None, version="1"):
        self.data = data
        self.set_empty_data()
        self._version = version
        self.set_version_as_str()
        self.set_index()

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, new_version):
        if new_version not in self.data.index:
            raise CashflowModelError(f"There is no version '{new_version}' in the Runplan.")
        self._version = new_version

    def set_empty_data(self):
        """Set minimal runplan if not provided by the user."""
        if self.data is None:
            self.data = pd.DataFrame({"version": ["1"]})

    def set_version_as_str(self):
        """Ensure that the 'version' column is a string."""
        if "version" not in self.data.columns:
            raise CashflowModelError("Runplan must have the 'version' column.")
        else:
            self.data["version"] = self.data["version"].astype(str)

    def set_index(self):
        """Set 'version' column as an index of the data frame."""
        self.data = self.data.set_index("version")

    def get(self, attribute):
        """Get a value from the runplan for the current version.

        Parameters
        ----------
        attribute : str
            Column name of the needed attribute.

        Returns
        -------
        scalar
        """
        if attribute not in self.data.columns:
            raise CashflowModelError(f"There is no column '{attribute}' in the runplan.")
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

    def __init__(self, data, name=None, settings=None):
        self.__class__.instances.append(self)
        self.data = data
        self.name = name
        self.settings = settings
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
        """Get value from the modelpoint for the current policy id and record.

        Parameters
        ----------
        attribute : str
            Column name of the needed attribute.

        Returns
        -------
        scalar
        """
        return self.policy_record[attribute].values[0]

    @property
    def policy_id(self):
        """Policy id of the currently evaluated policy. """
        return self._policy_id

    @policy_id.setter
    def policy_id(self, new_policy_id):
        """Set model point's policy id.

        Check if the policy id exists in the model point.
        Set policy data and size (number of records).
        Set record number back to zero.
        """
        self._policy_id = new_policy_id

        if new_policy_id not in self.data.index:
            raise CashflowModelError(f"There is no policy id '{new_policy_id}' in modelpoint '{self.name}'.")

        self.policy_data = self.data.loc[[new_policy_id]]
        self.size = self.policy_data.shape[0]
        self.record_num = 0

    @property
    def record_num(self):
        """Record number for the policies with multiple records. """
        return self._record_num

    @record_num.setter
    def record_num(self, new_record_num):
        """Set policy's record number (relevant for the policies with multiple records).

        Set policy record (row of policy data for the currently evaluated record number).
        """
        self._record_num = new_record_num
        self.policy_record = self.policy_data.iloc[[new_record_num]]

    def initialize(self):
        self.check_policy_id_col()
        self.check_unique_keys()
        self.set_index()
        self.policy_id = self.data.iloc[0][self.settings["POLICY_ID_COLUMN"]]

    def check_policy_id_col(self):
        policy_id_column = self.settings["POLICY_ID_COLUMN"]
        if policy_id_column not in self.data.columns:
            raise CashflowModelError(f"\nThere is no column '{policy_id_column}' in modelpoint '{self.name}'.")
        return True

    def check_unique_keys(self):
        policy_id_column = self.settings["POLICY_ID_COLUMN"]
        if self.name == "policy":
            if not self.data[policy_id_column].is_unique:
                msg = f"\nThe 'policy' modelpoint must have unique values in '{policy_id_column}' column."
                raise CashflowModelError(msg)
        return True

    def set_index(self):
        policy_id_column = self.settings["POLICY_ID_COLUMN"]
        self.data[policy_id_column] = self.data[policy_id_column].astype(str)
        self.data[policy_id_column + "_duplicate"] = self.data[policy_id_column]
        self.data = self.data.set_index(policy_id_column)
        self.data[policy_id_column] = self.data[policy_id_column + "_duplicate"]
        self.data = self.data.drop(columns=[policy_id_column + "_duplicate"])


class ModelVariable:
    """Model variable of a cash flow model.
    
    Model variable returns numbers and is t-dependent.
    Model variable is linked to a modelpoint and calculates results based on the formula.

    Attributes
    ----------
    name : str
        Name of the code variable.
    modelpoint : ModelPoint object
        Model point to which the variable is linked.
        User sets it directly in the model script, otherwise it is set to the primary model point.
    pol_dep : bool
        Should the variable be calculated for each policyholder or only once?
    assigned_formula : function
        Function attached using the @assign decorator.
    _formula : function
        The formula to calculate the results. It takes definition from assigned_formula.
        While setting, it checks if the formula is recursive.
    recursive : str
        States if the formula is recursive, possible values: 'forward', 'backward' and 'not_recursive'.
    settings : dict
        User settings from 'settings.py'.
    result : list
        List of n lists with m elements where: n = num of records for policy, m = num of projection months.
    runtime: float
        The runtime of the model variable in the model run (in seconds).
    children : list of model variables
        List of model variables that this variable is calling in its formula.
        Only relevant in the model context because model is linked to a group of variables.
    grandchildren : list of model variables
        Children and their descendants (children, grandchildren, grandgrandchildren and so on...).
    """
    instances = []

    def __init__(self, name=None, modelpoint=None, settings=None, pol_dep=True):
        self.__class__.instances.append(self)
        self.name = name
        self.modelpoint = modelpoint
        self.settings = settings
        self.pol_dep = pol_dep
        self.assigned_formula = None
        self._formula = None
        self.recursive = None
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

        return self.result[self.modelpoint.record_num][t]

    @property
    def formula(self):
        """Formula used to calculate result. """
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        """Set a formula to the model variable.

        Check if the formula has correct parameters.
        Set if the formula is recursive (and how).
        """
        params = inspect.signature(new_formula).parameters

        # Model variables should have parameter 't'
        if not (len(params) == 1 and "t" in params.keys()):
            msg = f"\nModel variable formula must have only one parameter: 't'. " \
                  f"Please check code for '{new_formula.__name__}'."
            raise CashflowModelError(msg)

        # The calculation varies if the model variable is recursive
        formula_source = inspect.getsource(new_formula)
        clean = utils.clean_formula_source(formula_source)
        self.recursive = utils.is_recursive(clean, self.name)
        self._formula = new_formula

    def clear(self):
        """Clear formula's cache. """
        if self.pol_dep:
            self.formula.cache_clear()

    def calculate(self):
        """Calculate result for all records of the policy. """
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        self.result = np.empty((self.modelpoint.size, t_calculation_max+1), dtype=float)

        for r in range(self.modelpoint.size):
            self.modelpoint.record_num = r
            self.clear()

            if self.recursive == "not_recursive":
                self.result[r, :] = [*map(self.formula, range(t_calculation_max+1))]
            elif self.recursive == "backward":
                for t in range(t_calculation_max, -1, -1):
                    self.result[r, t] = self.formula(t)
            else:
                for t in range(t_calculation_max+1):
                    self.result[r, t] = self.formula(t)

    def initialize(self, policy=None):
        if self.assigned_formula is None:
            msg = f"\nThe '{self.name}' variable has no formula. Please check the 'model.py' script."
            raise CashflowModelError(msg)

        if self.modelpoint is None:
            self.modelpoint = policy

        self.formula = self.assigned_formula

    def in_output(self, output_columns):
        return output_columns == [] or self.name in output_columns


class Constant:
    """Constant of a cash flow model.

    Constant can return either number or string and is t-independent.

    Attributes
    ----------
    name : str
        Name of the code variable.
    modelpoint : ModelPoint object
        Model point to which the variable is linked.
        User sets it directly in the model script, otherwise it is set to the primary model point.
    assigned_formula : function
        Function attached using the @assign decorator.
    _formula : function
        The formula to calculate the results. It takes definition from assigned_formula.
        While setting, it checks if the formula is recursive.
    result : list
        List of n lists with 1 element where: n = num of records for policy.
    runtime: float
        The runtime of the model variable in the model run (in seconds).
    children : list of model variables
        List of model variables that this variable is calling in its formula.
        Only relevant in the model context because model is linked to a group of variables.
    grandchildren : list of model variables
        Children and their descendants (children, grandchildren, grandgrandchildren and so on...).
    """
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
            return "C: NoName"
        return f"C: {self.name}"

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, r=None):
        # User might call lower order variable from higher order variable and specify record (r)
        if r is not None:
            try:
                return self.result[r]
            except IndexError:
                raise CashflowModelError(f"Unable to evaluate the '{self.name}' constant. "
                                         f"Tip: don't call constants with the time parameter.")

        return self.result[self.modelpoint.record_num]

    @property
    def formula(self):
        """Formula to calculate constant's value. """
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        """Set a formula.

        Check if formula doesn't have any parameters.
        """
        params = inspect.signature(new_formula).parameters
        if not (len(params) == 0):
            msg = f"\nFormula can't have any parameters. Please check code for '{new_formula.__name__}'."
            raise CashflowModelError(msg)
        self._formula = new_formula

    def clear(self):
        """Clear formula's cache. """
        self.formula.cache_clear()

    def calculate(self):
        """Calculate parameter's value for all records in the policy. """
        self.result = [None] * self.modelpoint.size
        for r in range(self.modelpoint.size):
            self.modelpoint.record_num = r
            self.clear()
            self.result[r] = self.formula()

    def initialize(self, policy=None):
        if self.assigned_formula is None:
            msg = f"\nThe '{self.name}' parameter has no formula. Please check the 'model.py' script."
            raise CashflowModelError(msg)

        if self.modelpoint is None:
            self.modelpoint = policy

        self.formula = self.assigned_formula

    def in_output(self, output_columns):
        return output_columns == [] or self.name in output_columns


class Model:
    """Actuarial cash flow model.
    
    Model combines constants, model variables and modelpoints.
    Model components (constants and variables) are ordered into a calculation queue.
    All variables are calculated for data of each policyholder in the modelpoints.

    Attributes
    ----------
    name : str
        Model's name
    variables : list
        List of model variables objects.
    constants : list
        List of constants objects.
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
    def __init__(self, name, variables, constants, modelpoints, settings):
        self.name = name
        self.variables = variables
        self.constants = constants
        self.modelpoints = modelpoints
        self.settings = settings
        self.components = variables + constants
        self.queue = []
        self.empty_output = None
        self.output = None

    def get_component_by_name(self, name):
        """Get a model component object by its name.

        Parameters
        ----------
        name : str
            Name of the model variable or parameter.

        Returns
        -------
        object of class ModelVariable or Constant
        """
        for component in self.components:
            if component.name == name:
                return component

    def get_modelpoint_by_name(self, name):
        """Get a model point object by its name.

        Parameters
        ----------
        name : str
            Name of the model point.

        Returns
        -------
        object of class ModelPoint
        """
        for modelpoint in self.modelpoints:
            if modelpoint.name == name:
                return modelpoint

    def set_children(self):
        """Set children of the model components. """
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
        """Set grandchildren of model components. """
        for component in self.components:
            component.grandchildren = list(component.children)
            i = 0
            while i < len(component.grandchildren):
                grandchild = component.grandchildren[i]
                component.grandchildren = utils.unique_extend(component.grandchildren, grandchild.children)
                i += 1

    def remove_from_grandchildren(self, removed_component):
        """Remove component from grandchildrens. """
        for component in self.components:
            if removed_component in component.grandchildren:
                component.grandchildren.remove(removed_component)

    def set_queue(self):
        """Set an ordrer in which model components should be evaluated. """
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
        """Create empty output to be populated with results. """
        empty_output = dict()
        aggregate = self.settings["AGGREGATE"]
        output_columns = self.settings["OUTPUT_COLUMNS"]

        # Each modelpoint has a separate output file
        for modelpoint in self.modelpoints:
            empty_output[modelpoint.name] = pd.DataFrame()
            empty_output[modelpoint.name]["t"] = None
            # Individual output contains record numbers
            if not aggregate:
                empty_output[modelpoint.name]["r"] = None

        # Aggregated output contains only variables
        # Individual output contains all components (variables and constants)
        if aggregate:
            output_variables = [v for v in self.variables if v.in_output(output_columns)]
            for output_variable in output_variables:
                empty_output[output_variable.modelpoint.name][output_variable.name] = None
        else:
            output_components = [c for c in self.components if c.in_output(output_columns)]
            for output_component in output_components:
                empty_output[output_component.modelpoint.name][output_component.name] = None

        self.empty_output = empty_output

    def clear_components(self):
        """Clear cache of all components."""
        for component in self.components:
            component.clear()

    def calculate_one_policy(self, row, n_pols, primary):
        """Calculate results for a policy currently indicated in the model point. """
        policy_id = primary.data.index[row]
        for modelpoint in self.modelpoints:
            modelpoint.policy_id = policy_id

        self.clear_components()

        policy_output = copy.deepcopy(self.empty_output)
        aggregate = self.settings["AGGREGATE"]
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], t_calculation_max)
        output_columns = self.settings["OUTPUT_COLUMNS"]

        for c in self.queue:
            start = time.time()
            try:
                c.calculate()
            except:
                raise CashflowModelError(f"Unable to evaluate '{c.name}'.")
            else:
                if c.in_output(output_columns):
                    # Variables are always in the output
                    if isinstance(c, ModelVariable):
                        if aggregate:
                            policy_output[c.modelpoint.name][c.name] = sum(c.result[:, :t_output_max+1])
                        else:
                            policy_output[c.modelpoint.name][c.name] = c.result[:, :t_output_max+1].flatten()

                    # Constants are added only to individual output
                    if isinstance(c, Constant) and not aggregate:
                        policy_output[c.modelpoint.name][c.name] = np.repeat(c.result, t_output_max+1)
            c.runtime += time.time() - start

        # Add time and record number to the individual output
        if not aggregate:
            for modelpoint in self.modelpoints:
                policy_output[modelpoint.name]["t"] = np.tile(np.arange(t_output_max+1), modelpoint.size)
                policy_output[modelpoint.name]["r"] = np.repeat(np.arange(1, modelpoint.size+1), t_output_max+1)

        updt(n_pols, row + 1)
        return policy_output

    def calculate_all_policies(self):
        """Calculate results for all policies. """
        output = copy.deepcopy(self.empty_output)
        aggregate = self.settings["AGGREGATE"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], self.settings["T_CALCULATION_MAX"])
        primary = self.get_modelpoint_by_name("policy")

        n_pols = len(primary)
        utils.print_log(f"Number of policies: {n_pols}")

        calculate = functools.partial(self.calculate_one_policy, n_pols=n_pols, primary=primary)
        policy_outputs = [*map(calculate, range(n_pols))]

        utils.print_log("Preparing results")
        for m in self.modelpoints:
            if aggregate:
                output[m.name] = sum(policy_output[m.name] for policy_output in policy_outputs)
                output[m.name]["t"] = np.arange(t_output_max+1)
            else:
                output[m.name] = pd.concat(policy_output[m.name] for policy_output in policy_outputs)

        self.output = output
        return output

    def run(self):
        """Orchestrate all steps of the cash flow model run. """
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
        utils.print_log(f"Finished. Elapsed time: {datetime.timedelta(seconds=round(end-start))}.")
        return timestamp
