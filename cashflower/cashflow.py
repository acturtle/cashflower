import functools
import time
import numpy as np
import pandas as pd

from .error import CashflowModelError
from .utils import get_object_by_name, print_log, split_to_ranges, updt


def variable():
    """Decorator"""
    def wrapper(func):
        # Variable must have parameter "t" or no parameters at all
        if func.__code__.co_argcount > 1:
            msg = f"Model variable must have maximally one parameter. Please review '{func.__name__}'."
            raise CashflowModelError(msg)

        # Parameter must be named "t"
        if func.__code__.co_argcount == 1:
            if not func.__code__.co_varnames[0] == 't':
                msg = f"The name of the parameter must be named 't'. Please review '{func.__name__}'."
                raise CashflowModelError(msg)

        # Create a variable
        if func.__code__.co_argcount == 0:
            variable = ConstantVariable(func)
        else:
            variable = Variable(func)

        # Variable is constant if it is t-independent
        if func.__code__.co_argcount == 0:
            variable.constant = True

        return variable
    return wrapper


class Variable:
    def __init__(self, func):
        self.func = func
        self.name = None
        self._t_max = None
        self.calc_direction = None
        self.calc_order = None
        self.cycle = False
        self.cycle_cache = set()
        self.result = None
        self.runtime = 0.0

    def __repr__(self):
        return f"V: {self.func.__name__}"

    def __call__(self, t=None):
        if t < 0 or t > self.t_max:
            msg = f"Variable '{self.name}' has been called for period '{t}' which is outside of calculation range."
            raise CashflowModelError(msg)

        # In cycle, the calculation order might not be known
        if self.cycle and t not in self.cycle_cache:
            self.cycle_cache.add(t)
            self.result[t] = self.func(t)

        return self.result[t]

    @property
    def t_max(self):
        return self._t_max

    @t_max.setter
    def t_max(self, new_t_max):
        self._t_max = new_t_max
        self.result = np.array([None for _ in range(0, self.t_max + 1)])

    def calculate_t(self, t):
        # This method is used for cycles only
        if t not in self.cycle_cache:
            self.cycle_cache.add(t)
            self.result[t] = self.func(t)

    def calculate(self):
        if self.calc_direction == 0:
            self.result = np.array([*map(self.func, range(self.t_max + 1))])
        elif self.calc_direction == 1:
            for t in range(self.t_max + 1):
                self.result[t] = self.func(t)
        elif self.calc_direction == -1:
            for t in range(self.t_max, -1, -1):
                self.result[t] = self.func(t)
        else:
            raise CashflowModelError(f"Incorrect calculation direction {self.calc_direction}")


class ConstantVariable(Variable):
    def __init__(self, func):
        Variable.__init__(self, func)

    def __repr__(self):
        return f"CV: {self.func.__name__}"

    def __call__(self, t=None):
        # In the cycle, we don't know exact calculation order
        if self.cycle:
            return self.func()

        return self.result[0]

    def calculate_t(self, t):
        self.result[t] = self.func()

    def calculate(self):
        value = self.func()
        self.result = np.array([value for _ in range(0, self.t_max + 1)])


class Runplan:
    """Runplan of the cash flow model."""
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
        """Get a value from the runplan for the current version."""
        if attribute not in self.data.columns:
            raise CashflowModelError(f"There is no column '{attribute}' in the runplan.")
        return self.data.loc[self.version][attribute]


class ModelPointSet:
    """Set of model points."""

    def __init__(self, data, name=None, settings=None):
        self.data = data
        self.name = name
        self.settings = settings
        self._id = None
        self.model_point_data = None

    def __repr__(self):
        return f"MPS: {self.name}"

    def __len__(self):
        return self.data.shape[0]

    @functools.lru_cache()
    def get(self, attribute, record_num=0):
        if self.id is None:
            return None
        return self.model_point_data.iloc[record_num][attribute]

    @property
    def id(self):
        """Current model point's id."""
        return self._id

    @id.setter
    def id(self, new_id):
        """Set model point's id and corresponding attributes."""
        if new_id in self.data.index:
            self._id = new_id
            self.model_point_data = self.data.loc[[new_id]]
        else:
            self._id = None
        self.get.cache_clear()

    def initialize(self):
        """Name and settings are not present while creating object, so additional initialization is needed."""
        self.perform_checks()
        self.set_index()
        self.id = self.data.iloc[0][self.settings["ID_COLUMN"]]

    def perform_checks(self):
        # Check ID columns
        id_column = self.settings["ID_COLUMN"]
        if id_column not in self.data.columns:
            raise CashflowModelError(f"\nThere is no column '{id_column}' in model_point_set '{self.name}'.")

        # Check unique keys in main
        id_column = self.settings["ID_COLUMN"]
        if self.name == "main":
            if not self.data[id_column].is_unique:
                msg = f"\nThe 'main' model_point_set must have unique values in '{id_column}' column."
                raise CashflowModelError(msg)

        return True

    def set_index(self):
        id_column = self.settings["ID_COLUMN"]
        self.data[id_column] = self.data[id_column].astype(str)
        self.data[id_column + "_duplicate"] = self.data[id_column]
        self.data = self.data.set_index(id_column)
        self.data[id_column] = self.data[id_column + "_duplicate"]
        self.data = self.data.drop(columns=[id_column + "_duplicate"])


class Model:
    """Actuarial cash flow model.
    Model combines model variables and model point sets."""
    def __init__(self, name, variables, model_point_sets, settings, cpu_count=None):
        self.name = name
        self.variables = variables
        self.model_point_sets = model_point_sets
        self.settings = settings
        self.cpu_count = cpu_count
        self.output = None

    def run(self, part=None):
        """Orchestrate all steps of the cash flow model run."""
        one_core = part == 0 or part is None  # single or first part
        print_log(f"Building model '{self.name}'", one_core)

        # Iterate over model points
        main = get_object_by_name(self.model_point_sets, "main")
        print_log(f"Total number of model points: {main.data.shape[0]}", one_core)
        if one_core and self.settings["MULTIPROCESSING"]:
            if len(main) > self.cpu_count:
                print_log(f"Multiprocessing on {self.cpu_count} cores")
                print_log(f"Calculation of ca. {len(main) // self.cpu_count} model points per core")

        # Set calculation ranges for multiprocessing
        range_start, range_end = None, None
        if self.settings["MULTIPROCESSING"]:
            main_ranges = split_to_ranges(len(main), self.cpu_count)
            # Number of model points is lower than the number of cpus, only calculate on the 1st core
            if part >= len(main_ranges):
                return None
            range_start, range_end = main_ranges[part]

        # Create partial calculation function for map
        progressbar_max = len(main) if range_end is None else range_end
        p = functools.partial(self.calculate_model_point, one_core=one_core, progressbar_max=progressbar_max)

        # Perform calculations
        if self.settings["MULTIPROCESSING"] is False:
            results = [*map(p, range(len(main)))]
        else:
            results = [*map(p, range(range_start, range_end))]

        # Concatenate or aggregate results
        if len(self.settings["OUTPUT_COLUMNS"]) == 0:
            output_columns = [variable.name for variable in self.variables]
        else:
            output_columns = self.settings["OUTPUT_COLUMNS"]

        if self.settings["AGGREGATE"] is False:
            total_data = np.transpose(functools.reduce(lambda a, b: np.concatenate((a, b), axis=1), results))
            result = pd.DataFrame(data=total_data, columns=output_columns)
        else:
            total_data = np.transpose(functools.reduce(lambda a, b: a + b, results))
            result = pd.DataFrame(data=total_data, columns=output_columns)

        # Get diagnostic file
        diagnostic = None
        if self.settings["SAVE_DIAGNOSTIC"]:
            diagnostic = pd.DataFrame({
                "variable": [v.name for v in self.variables],
                "calc_order": [v.calc_order for v in self.variables],
                "cycle": [v.cycle for v in self.variables],
                "calc_direction": [v.calc_direction for v in self.variables],
                "runtime": [v.runtime for v in self.variables]
            })

        return result, diagnostic

    def calculate_model_point(self, row, one_core, progressbar_max):
        main = get_object_by_name(self.model_point_sets, "main")

        # Set model point's id
        model_point_id = main.data.index[row]
        for model_point_set in self.model_point_sets:
            model_point_set.id = model_point_id

        # Perform calculations
        max_calc_order = self.variables[-1].calc_order
        for calc_order in range(1, max_calc_order + 1):
            # Either a single variable or a cycle
            variables = [variable for variable in self.variables if variable.calc_order == calc_order]
            # Single
            if len(variables) == 1:
                variable = variables[0]
                start = time.time()
                variable.calculate()
                variable.runtime += time.time() - start
            # Cycle
            else:
                start = time.time()
                first_variable = variables[0]
                calc_direction = first_variable.calc_direction
                if calc_direction in (0, 1):
                    for t in range(self.settings["T_MAX_CALCULATION"] + 1):
                        for variable in variables:
                            variable.calculate_t(t)
                else:
                    for t in range(self.settings["T_MAX_CALCULATION"], -1, -1):
                        for variable in variables:
                            variable.calculate_t(t)
                end = time.time()
                avg_runtime = (end-start)/len(variables)
                for variable in variables:
                    variable.runtime += avg_runtime

        # Clear cache of cycle variables
        for variable in self.variables:
            if variable.cycle:
                variable.cycle_cache.clear()

        # Get results and trim for T_MAX_OUTPUT,results may contain subset of columns
        if len(self.settings["OUTPUT_COLUMNS"]) > 0:
            mp_results = np.array([v.result[:self.settings["T_MAX_OUTPUT"]+1] for v in self.variables if v.name in self.settings["OUTPUT_COLUMNS"]])
        else:
            mp_results = np.array([v.result[:self.settings["T_MAX_OUTPUT"]+1] for v in self.variables])

        # Update progessbar
        if one_core:
            updt(progressbar_max, row + 1)

        return mp_results
