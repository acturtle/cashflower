import copy
import datetime
import functools
import inspect
import numpy as np
import os
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

    def set_empty_output(self):
        """Create empty output to be populated with results. """
        empty_output = dict()
        aggregate = self.settings["AGGREGATE"]
        output_columns = self.settings["OUTPUT_COLUMNS"]

        # Each model_point_set has a separate output file
        for modelpointset in self.model_point_sets:
            empty_output[modelpointset.name] = pd.DataFrame()
            empty_output[modelpointset.name]["t"] = None
            # Individual output contains record numbers
            if not aggregate:
                empty_output[modelpointset.name]["r"] = None

        # Aggregated output contains only variables
        # Individual output contains all components (variables and constants)
        if aggregate:
            output_variables = [v for v in self.variables if v.in_output(output_columns)]
            for output_variable in output_variables:
                empty_output[output_variable.model_point_set.name][output_variable.name] = None
        else:
            output_components = [c for c in self.components if c.in_output(output_columns)]
            for output_component in output_components:
                empty_output[output_component.model_point_set.name][output_component.name] = None

        self.empty_output = empty_output

    def initialize(self):
        self.set_empty_output()
        self.set_children()
        self.set_grandchildren()
        self.set_queue()

    def calculate_single_model_point(self, row, pb_max, main, one_core=None):
        """Calculate results for a model point currently indicated in the model point set."""
        model_point_id = main.model_point_set_data.index[row]
        for model_point_set in self.model_point_sets:
            model_point_set.id = model_point_id

        model_point_output = copy.deepcopy(self.empty_output)
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
                # User can choose output columns
                if c.in_output(output_columns):
                    # Variables are always in the output (individual and aggregate)
                    if isinstance(c, ModelVariable):
                        if aggregate:
                            model_point_output[c.model_point_set.name][c.name] = sum(c.result[:, :t_output_max + 1])
                        else:
                            model_point_output[c.model_point_set.name][c.name] = c.result[:, :t_output_max + 1].flatten()
                    # Constants are added only to individual output
                    if isinstance(c, Constant) and not aggregate:
                        model_point_output[c.model_point_set.name][c.name] = np.repeat(c.result, t_output_max + 1)
            c.runtime += time.time() - start

        # Add time and record number to the individual output
        if not aggregate:
            for model_point_set in self.model_point_sets:
                model_point_output[model_point_set.name]["t"] = np.tile(np.arange(t_output_max + 1), model_point_set.model_point_size)
                model_point_output[model_point_set.name]["r"] = np.repeat(np.arange(1, model_point_set.model_point_size + 1), t_output_max + 1)

        if one_core:
            updt(pb_max, row + 1)

        return model_point_output

    def calculate(self, range_start=None, range_end=None):
        """Calculate results for all model points."""
        # Configuration
        model_output = copy.deepcopy(self.empty_output)
        aggregate = self.settings["AGGREGATE"]
        t_output_max = min(self.settings["T_OUTPUT_MAX"], self.settings["T_CALCULATION_MAX"])
        main = get_object_by_name(self.model_point_sets, "main")

        one_core = range_start == 0 or range_start is None

        # Calculate formulas
        n_pols = len(main)
        pb_max = n_pols if range_end is None else range_end
        calculate = functools.partial(self.calculate_single_model_point, pb_max=pb_max, main=main, one_core=one_core)
        if range_start is None:
            model_point_outputs = [*map(calculate, range(n_pols))]
        else:
            model_point_outputs = [*map(calculate, range(range_start, range_end))]

        # Merge results from single model points
        if one_core:
            print_log("Preparing results")

        for model_point_set in self.model_point_sets:
            if aggregate:
                model_output[model_point_set.name] = sum(model_point_output[model_point_set.name] for model_point_output in model_point_outputs)
                if not self.settings["MULTIPROCESSING"]:
                    model_output[model_point_set.name]["t"] = np.arange(t_output_max + 1)
            else:
                model_output[model_point_set.name] = pd.concat(model_point_output[model_point_set.name] for model_point_output in model_point_outputs)

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
            if main.model_point_set_data.shape[0] > self.cpu_count:
                print_log(f"Multiprocessing on {self.cpu_count} cores")
                print_log(f"Calculation of ca. {len(main) // self.cpu_count} model points per core")
                print_log("The progressbar for the calculations on the 1st core:")

        # In multiprocessing mode, the subset of policies is calculated
        if self.settings["MULTIPROCESSING"]:
            main_ranges = split_to_ranges(len(main), self.cpu_count)

            # Number of model points is lower than the number of cpus, only calculate on the 1st core
            if part >= len(main_ranges):
                return None

            main_range = main_ranges[part]
            self.calculate(range_start=main_range[0], range_end=main_range[1])
        # Otherwise, all policies are calculated
        else:
            self.calculate()

        return self.output

    def save(self):
        """Only for single core (no multiprocessing)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not os.path.exists("output"):
            os.makedirs("output")

        # Save output to csv
        if self.settings["SAVE_OUTPUT"]:
            print_log("Saving output:")
            for model_point_set in self.model_point_sets:
                filepath = f"output/{timestamp}_{model_point_set.name}.csv"
                model_point_set_output = self.output.get(model_point_set.name)
                column_names = [col for col in model_point_set_output.columns.values.tolist() if col not in ["t", "r"]]
                if len(column_names) > 0:
                    print(f"{' ' * 10} {filepath}")
                    model_point_set_output.to_csv(filepath, index=False)

        # Save runtime
        if self.settings["SAVE_RUNTIME"]:
            data = [(c.name, c.runtime) for c in self.components]
            runtime = pd.DataFrame(data, columns=["component", "runtime"])
            runtime.to_csv(f"output/{timestamp}_runtime.csv", index=False)
            print(f"{' '*10} output/{timestamp}_runtime.csv")

        print_log("Finished")
        return timestamp
