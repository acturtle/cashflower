import copy
import functools
import inspect
import numpy as np
import time
import pandas as pd
import sys


from .utils import *


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


def get_col_dict(model_point_sets, variables, constants, settings):
    """
    | main | ModelVariable = ["a", "b"]
    |      | Constant      = ["c"]
    | fund | ModelVariable = ["d"]
    |      | Constant      = []
    """
    col_dict = {}
    for model_point_set in model_point_sets:
        col_dict[model_point_set.name] = {}
        col_dict[model_point_set.name]["ModelVariable"] = []
        col_dict[model_point_set.name]["Constant"] = []

    # A subset of output columns has been chosen
    if len(settings["OUTPUT_COLUMNS"]) > 0:
        variables = [variable for variable in variables if variable.name in settings["OUTPUT_COLUMNS"]]
        constants = [constant for constant in constants if constant.name in settings["OUTPUT_COLUMNS"]]

    for variable in variables:
        col_dict[variable.model_point_set.name]["ModelVariable"].append(variable.name)

    # Aggregate output does not contain Constants (because they don't add up)
    if not settings["AGGREGATE"]:
        for constant in constants:
            col_dict[constant.model_point_set.name]["Constant"].append(constant.name)

    return col_dict


def col_dict_to_model_point_output(col_dict, settings, records):
    """
    | main | ModelVariable = matrix(n1 x m1)
    |      | Constant      = matrix(n2 x m2)
    | fund | ModelVariable = matrix(n3 x m3)
    |      | Constant      = matrix(n4 x m4)
    m_x = num_components (may be zero)
    n_x = t_output_max (* num_records if individual output)
    """
    model_point_output = copy.deepcopy(col_dict)

    for model_point_set_name in col_dict.keys():
        num_records = 1 if settings["AGGREGATE"] else records[model_point_set_name]
        n = (settings["T_OUTPUT_MAX"]+1) * num_records

        m = len(col_dict[model_point_set_name]["ModelVariable"])
        model_point_output[model_point_set_name]["ModelVariable"] = np.zeros((n, m), dtype=np.float64)

        m = len(col_dict[model_point_set_name]["Constant"])
        model_point_output[model_point_set_name]["Constant"] = np.zeros((n, m), dtype=np.object_)
    return model_point_output


def flatten_col_dict(col_dict):
    lst = []
    for key1 in col_dict.keys():
        for key2 in col_dict[key1]:
            lst.append(col_dict[key1][key2])
    return [item for sublist in lst for item in sublist]


class CashflowModelError(Exception):
    pass


class Runplan:
    """Runplan of the cash flow model.

    Attributes
    ----------
    data : model_point_set_data frame
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
        """Set 'version' column as an index of the model_point_set_data frame."""
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


class ModelPointSet:
    """Set of model points.

    Attributes
    ----------
    data : model_point_set_data frame
        Data containing model points.
    name : str
        Used in the output filename. Set in get_model_input().
    settings : dict
        User settings. Model point uses ID_COLUMN setting. Set in get_model_input().
    _id : str
        Value to identify the model point in the column defined by ID_COLUMN setting.
        Looped over in model.calculated_policies().
    _model_point_record_num : int
        Record number - relevant when there are multiple records for the same model point.
        Looped over in model_variable.calculate().
    model_point_data : model_point_set_data frame
        Row(s) of model_point_set_data for the current model point.
    model_point_size : int
        Number of rows of model_point_set_data for all model points.
    model_point_record_data : model_point_set_data frame
        Row of model_point_set_data for the current model point and record.
    """

    instances = []

    def __init__(self, data, name=None, settings=None):
        self.__class__.instances.append(self)
        self.model_point_set_data = data
        self.name = name
        self.settings = settings
        self._id = None
        self._model_point_record_num = None
        self.model_point_data = None
        self.model_point_size = 0
        self.model_point_record_data = None

    def __repr__(self):
        return f"ModelPointSet: {self.name}"

    def __len__(self):
        return self.model_point_set_data.shape[0]

    def get(self, attribute):
        """Get value from the the current record."""
        return self.model_point_record_data[attribute].values[0]

    @property
    def id(self):
        """Current model point's id."""
        return self._id

    @id.setter
    def id(self, new_id):
        """Set model point's id and corresponding attributes."""
        self._id = new_id

        if new_id not in self.model_point_set_data.index:
            raise CashflowModelError(f"There is no id '{new_id}' in model_point_set '{self.name}'.")

        self.model_point_data = self.model_point_set_data.loc[[new_id]]
        self.model_point_size = self.model_point_data.shape[0]
        self.model_point_record_num = 0

    @property
    def model_point_record_num(self):
        """Current model point's record number (model point can have multiple records)."""
        return self._model_point_record_num

    @model_point_record_num.setter
    def model_point_record_num(self, new_record_num):
        """Set model point's record number and data."""
        self._model_point_record_num = new_record_num
        self.model_point_record_data = self.model_point_data.iloc[[new_record_num]]

    def initialize(self):
        self.check_id_col()
        self.check_unique_keys()
        self.set_index()
        self.id = self.model_point_set_data.iloc[0][self.settings["ID_COLUMN"]]

    def check_id_col(self):
        id_column = self.settings["ID_COLUMN"]
        if id_column not in self.model_point_set_data.columns:
            raise CashflowModelError(f"\nThere is no column '{id_column}' in model_point_set '{self.name}'.")
        return True

    def check_unique_keys(self):
        id_column = self.settings["ID_COLUMN"]
        if self.name == "main":
            if not self.model_point_set_data[id_column].is_unique:
                msg = f"\nThe 'main' model_point_set must have unique values in '{id_column}' column."
                raise CashflowModelError(msg)
        return True

    def set_index(self):
        id_column = self.settings["ID_COLUMN"]
        self.model_point_set_data[id_column] = self.model_point_set_data[id_column].astype(str)
        self.model_point_set_data[id_column + "_duplicate"] = self.model_point_set_data[id_column]
        self.model_point_set_data = self.model_point_set_data.set_index(id_column)
        self.model_point_set_data[id_column] = self.model_point_set_data[id_column + "_duplicate"]
        self.model_point_set_data = self.model_point_set_data.drop(columns=[id_column + "_duplicate"])


class ModelVariable:
    """Model variable of a cash flow model.
    Model variable returns numbers and is t-dependent.
    Model variable is linked to a model_point_set and calculates results based on the formula.

    Attributes
    ----------
    name : str
        Name of the code variable.
    model_point_set : ModelPointSet object
        Model point to which the variable is linked.
        User sets it directly in the model script, otherwise it is set to the main model point.
    mp_dep : bool
        Should the variable be calculated for each model point or only once?
    calc_array : bool
        Is the calculation arrayized?
    assigned_formula : function
        Function attached using the @assign decorator.
    _formula : function
        The formula to calculate the results. It takes definition from assigned_formula.
        While setting, it checks if the formula is recursive.
    recursive : str
        States if the formula is recursive, possible values: 'forward', 'backward' and 'not_recursive'.
    settings : dict
        User settings from 'settings.py'.
    result : numpy array
        List of n lists with m elements where: n = num of model point records, m = num of projection months.
    runtime: float
        The runtime of the model variable in the model run (in seconds).
    children : list of model variables
        List of model variables that this variable is calling in its formula.
        Only relevant in the model context because model is linked to a group of variables.
    grandchildren : list of model variables
        Children and their descendants (children, grandchildren, grandgrandchildren and so on...).
    """
    instances = []

    def __init__(self, name=None, model_point_set=None, settings=None, mp_dep=True, calc_array=False):
        self.__class__.instances.append(self)
        self.name = name
        self.model_point_set = model_point_set
        self.settings = settings
        self.mp_dep = mp_dep
        self.calc_array = calc_array
        self.assigned_formula = None
        self._formula = None
        self.recursive = None
        self.result = None
        self.runtime = 0
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        return f"ModelVariable: {self.name}"

    def __lt__(self, other):
        return len(self.grandchildren) < len(other.grandchildren)

    def __call__(self, t=None, r=None):
        if t is None:
            return self.result[self.model_point_set.model_point_record_num, :]

        if t < 0 or t > self.settings["T_CALCULATION_MAX"]:
            return 0

        # User might call lower order variable from higher order variable and specify record (r)
        if r is not None:
            return self.result[r, t]

        return self.result[self.model_point_set.model_point_record_num, t]

    @property
    def formula(self):
        """Formula used to calculate result. """
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        """Set a formula to the model variable."""
        params = inspect.signature(new_formula).parameters

        # Model variables should have parameter 't'
        if not self.calc_array:
            if not (len(params) == 1 and "t" in params.keys()):
                msg = f"\nModel variable formula must have only one parameter: 't'. " \
                      f"Please check code for '{new_formula.__name__}'."
                raise CashflowModelError(msg)
        else:
            if not (len(params) == 0):
                msg = f"\nFormula for model variable with calc_array can't have any parameters. " \
                      f"Please check code for '{new_formula.__name__}'."
                raise CashflowModelError(msg)

        # The calculation varies if the model variable is recursive
        formula_source = inspect.getsource(new_formula)
        clean = clean_formula_source(formula_source)
        self.recursive = is_recursive(clean, self.name)
        self._formula = new_formula

    def clear(self):
        """Clear formula's cache. """
        if self.mp_dep:
            self.formula.cache_clear()

    def calculate(self):
        """Calculate result for all records of the model point."""
        t_calculation_max = self.settings["T_CALCULATION_MAX"]
        self.result = np.empty((self.model_point_set.model_point_size, t_calculation_max + 1), dtype=float)

        for r in range(self.model_point_set.model_point_size):
            self.clear()
            self.model_point_set.model_point_record_num = r

            # Formula returns an array
            if self.calc_array:
                self.result[r, :] = self.formula()

            # Formula returns value for each `t` separately
            else:
                # not recursive
                if self.recursive == 0:
                    self.result[r, :] = [*map(self.formula, range(t_calculation_max+1))]
                # recursive forward
                elif self.recursive == 1:
                    for t in range(t_calculation_max+1):
                        self.result[r, t] = self.formula(t)
                # recursive backward
                else:
                    for t in range(t_calculation_max, -1, -1):
                        self.result[r, t] = self.formula(t)

    def initialize(self, main=None):
        if self.assigned_formula is None:
            msg = f"\nThe '{self.name}' variable has no formula. Please check the 'model.py' script."
            raise CashflowModelError(msg)

        if self.model_point_set is None:
            self.model_point_set = main

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
    model_point_set : ModelPointSet object
        Model point to which the variable is linked.
        User sets it directly in the model script, otherwise it is set to the primary model point.
    assigned_formula : function
        Function attached using the @assign decorator.
    _formula : function
        The formula to calculate the results. It takes definition from assigned_formula.
        While setting, it checks if the formula is recursive.
    result : list
        List of n lists with 1 element where: n = num of model point records.
    runtime: float
        The runtime of the model variable in the model run (in seconds).
    children : list of model variables
        List of model variables that this variable is calling in its formula.
        Only relevant in the model context because model is linked to a group of variables.
    grandchildren : list of model variables
        Children and their descendants (children, grandchildren, grandgrandchildren and so on...).
    """
    def __init__(self, name=None, model_point_set=None, mp_dep=True):
        self.name = name
        self.model_point_set = model_point_set
        self.mp_dep = mp_dep
        self.assigned_formula = None
        self._formula = None
        self.result = None
        self.runtime = 0
        self.children = []
        self.grandchildren = []

    def __repr__(self):
        return f"Constant: {self.name}"

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

        return self.result[self.model_point_set.model_point_record_num]

    @property
    def formula(self):
        """Formula to calculate constant's value."""
        return self._formula

    @formula.setter
    def formula(self, new_formula):
        """Set a formula. Check if formula doesn't have any parameters."""
        params = inspect.signature(new_formula).parameters
        if not (len(params) == 0):
            msg = f"\nFormula can't have any parameters. Please check code for '{new_formula.__name__}'."
            raise CashflowModelError(msg)
        self._formula = new_formula

    def clear(self):
        """Clear formula's cache. """
        if self.mp_dep:
            self.formula.cache_clear()

    def calculate(self):
        """Calculate constant's value for all records in the model point."""
        self.result = [None] * self.model_point_set.model_point_size
        for r in range(self.model_point_set.model_point_size):
            self.clear()
            self.model_point_set.model_point_record_num = r
            self.result[r] = self.formula()

    def initialize(self, main=None):
        if self.assigned_formula is None:
            msg = f"\nThe '{self.name}' parameter has no formula. Please check the 'model.py' script."
            raise CashflowModelError(msg)

        if self.model_point_set is None:
            self.model_point_set = main

        self.formula = self.assigned_formula

    def in_output(self, output_columns):
        return output_columns == [] or self.name in output_columns


class Model:
    """Actuarial cash flow model.
    Model combines model variables, constants and model point sets.
    Model components (constants and variables) are ordered into a calculation queue.

    Attributes
    ----------
    name : str
        Model's name
    variables : list
        List of model variables objects.
    constants : list
        List of constants objects.
    model_point_sets : list
        List of model point objects.
    settings : dict
        User settings.
    queue : list
        List of model variables in an order in which they should be calculated.
    empty_output : dict
        Empty dict with keys prepared for output
    output : dict
        Dict with key = model_point_sets, values = model_point_set_data frames (columns for model variables).
    """
    def __init__(self, name, variables, constants, model_point_sets, settings, cpu_count=None):
        self.name = name
        self.variables = variables
        self.constants = constants
        self.model_point_sets = model_point_sets
        self.settings = settings
        self.components = variables + constants
        self.queue = []
        self.empty_output = None
        self.output = None
        self.cpu_count = cpu_count

    def set_children(self):
        """Set children of the model components. """
        component_names = [component.name for component in self.components]
        for component in self.components:
            formula_source = inspect.getsource(component.formula)
            cleaned_formula_source = clean_formula_source(formula_source)
            child_names = list_called_funcs(cleaned_formula_source, component_names)
            component.children = [get_object_by_name(self.components, n) for n in child_names if n != component.name]

    def set_grandchildren(self):
        """Set grandchildren of model components. """
        for component in self.components:
            component.grandchildren = list(component.children)
            i = 0
            while i < len(component.grandchildren):
                grandchild = component.grandchildren[i]
                component.grandchildren = unique_extend(component.grandchildren, grandchild.children)
                i += 1

    def remove_from_grandchildren(self, removed_component):
        """Remove component from grandchildrens. """
        for component in self.components:
            if removed_component in component.grandchildren:
                component.grandchildren.remove(removed_component)

    def set_queue(self):
        """Set an ordrer in which model components should be evaluated."""
        queue = []

        # User has chosen components, so there is no need to calculate all of them
        if len(self.settings["OUTPUT_COLUMNS"]) > 0:
            components = []
            for component_name in self.settings["OUTPUT_COLUMNS"]:
                component = get_object_by_name(self.components, component_name)
                components = unique_append(components, component)
                components = unique_extend(components, component.grandchildren)
            components = sorted(components)
        else:
            components = sorted(self.components)

        while components:
            component = components[0]

            if len(component.grandchildren) != 0:
                cycle = get_cycle(component, rest=components)
                msg = f"Cycle of model components detected. Please review:\n {cycle_to_str(cycle)}"
                raise CashflowModelError(msg)

            queue.append(component)
            self.remove_from_grandchildren(component)
            components.remove(component)
            components = sorted(components)
        self.queue = queue

    def initialize(self):
        self.set_children()
        self.set_grandchildren()
        self.set_queue()

    def calculate_model_point(self, row, pb_max, main, col_dict, one_core=None):
        """Calculate results for a model point currently indicated in the model point set."""
        model_point_id = main.model_point_set_data.index[row]
        records = {}
        for model_point_set in self.model_point_sets:
            model_point_set.id = model_point_id
            records[model_point_set.name] = model_point_set.model_point_data.shape[0]

        model_point_output = col_dict_to_model_point_output(col_dict, self.settings, records)
        col_components = flatten_col_dict(col_dict)

        for c in self.queue:
            start = time.time()
            try:
                c.calculate()
            except:
                raise CashflowModelError(f"Unable to evaluate '{c.name}'.")

            if c.name in col_components:
                if isinstance(c, ModelVariable):
                    index = col_dict[c.model_point_set.name]["ModelVariable"].index(c.name)
                    if self.settings["AGGREGATE"]:
                        result = sum(c.result[:, :self.settings["T_OUTPUT_MAX"] + 1])
                    else:
                        result = (c.result[:, :self.settings["T_OUTPUT_MAX"] + 1]).flatten()
                    model_point_output[c.model_point_set.name]["ModelVariable"][:, index] = result
                if isinstance(c, Constant):
                    index = col_dict[c.model_point_set.name]["Constant"].index(c.name)
                    result = np.repeat(c.result, self.settings["T_OUTPUT_MAX"] + 1)
                    result = result.astype(np.object_, copy=False)
                    model_point_output[c.model_point_set.name]["Constant"][:, index] = result
            c.runtime += time.time() - start

        if one_core:
            updt(pb_max, row + 1)

        return model_point_output

    def calculate_model(self, range_start=None, range_end=None):
        """Calculate results for all model points."""
        main = get_object_by_name(self.model_point_sets, "main")
        one_core = range_start == 0 or range_start is None

        # Calculate model points
        num_mp = len(main)
        pb_max = num_mp if range_end is None else range_end
        col_dict = get_col_dict(self.model_point_sets, self.variables, self.constants, self.settings)
        p = functools.partial(self.calculate_model_point, pb_max=pb_max, main=main, col_dict=col_dict, one_core=one_core)
        if range_start is None:
            model_point_outputs = [*map(p, range(num_mp))]
        else:
            model_point_outputs = [*map(p, range(range_start, range_end))]

        # Merge results from model points
        if one_core:
            print_log("Preparing results")

        model_output = {}
        for key in col_dict.keys():
            if self.settings["AGGREGATE"]:
                columns = col_dict[key]["ModelVariable"]
                if len(columns) > 0:
                    data = sum(mpo[key]["ModelVariable"] for mpo in model_point_outputs)
                    model_output[key] = pd.DataFrame(data, columns=col_dict[key]["ModelVariable"])
            else:
                columns = col_dict[key]["Constant"] + col_dict[key]["ModelVariable"]
                if len(columns) > 0:
                    data1 = np.concatenate([mpo[key]["Constant"] for mpo in model_point_outputs], axis=0)
                    data2 = np.concatenate([mpo[key]["ModelVariable"] for mpo in model_point_outputs], axis=0)
                    data = np.concatenate([data1, data2], axis=1)
                    model_output[key] = pd.DataFrame(data, columns=columns)

                    # Add records
                    model_point_set = get_object_by_name(self.model_point_sets, key)
                    ids = model_point_set.model_point_set_data[self.settings["ID_COLUMN"]]
                    if range_start is not None:
                        ids = ids[range_start:range_end]
                    records = lst_to_records(ids)
                    model_output[key].insert(0, "r", np.repeat(records, self.settings["T_OUTPUT_MAX"]+1))

        self.output = model_output
        return model_output

    def run(self, part=None):
        """Orchestrate all steps of the cash flow model run."""
        one_core = part == 0 or part is None

        if one_core:
            print_log(f"Start run for model '{self.name}'")

        # Prepare the order of variables for the calculation
        self.initialize()

        # Inform on the number of model points
        main = get_object_by_name(self.model_point_sets, "main")
        if one_core:
            print_log(f"Total number of model points: {main.model_point_set_data.shape[0]}")
        if part == 0:
            # Runtime is not saved when multiprocessing
            if self.settings["SAVE_RUNTIME"]:
                print_log(f"The SAVE_RUNTIME setting is not applicable for multiprocessing.\n"
                          f"{' '*10} Set the MULTIPROCESSING setting to 'False' to save the runtime.")
            if len(main) > self.cpu_count:
                print_log(f"Multiprocessing on {self.cpu_count} cores")
                print_log(f"Calculation of ca. {len(main) // self.cpu_count} model points per core")
                print_log("The progressbar for the calculations on the 1st core:")

        # Calculate all or subset of model points
        if self.settings["MULTIPROCESSING"]:
            main_ranges = split_to_ranges(len(main), self.cpu_count)

            # Number of model points is lower than the number of cpus, only calculate on the 1st core
            if part >= len(main_ranges):
                return None

            main_range = main_ranges[part]
            model_output = self.calculate_model(range_start=main_range[0], range_end=main_range[1])
        else:
            model_output = self.calculate_model()

        # Get runtime
        runtime = None
        if self.settings["SAVE_RUNTIME"]:
            runtime = pd.DataFrame({
                "component": [c.name for c in self.components],
                "runtime": [c.runtime for c in self.components]
            })

        return model_output, runtime
