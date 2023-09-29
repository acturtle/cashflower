import functools
import time
import multiprocessing
import numpy as np
import pandas as pd
import psutil

from .error import CashflowModelError
from .utils import get_object_by_name, print_log, split_to_ranges, updt


def get_variable_type(v):
    if isinstance(v, ConstantVariable):
        return "constant"
    elif isinstance(v, ArrayVariable):
        return "array"
    else:
        return "default"


def variable(array=False):
    """Transform a function with decorator into an object of class Variable"""
    def wrapper(func):
        # Variable has maximally 1 parameter
        if func.__code__.co_argcount > 1:
            msg = f"Error in '{func.__name__}': The model variable should have at most one parameter."
            raise CashflowModelError(msg)

        # Parameter must be named "t"
        if func.__code__.co_argcount == 1:
            if not func.__code__.co_varnames[0] == 't':
                msg = f"Error in '{func.__name__}': The parameter should be named 't'."
                raise CashflowModelError(msg)

        # Array variables don't have parameters
        if array and not func.__code__.co_argcount == 0:
            msg = f"Error in '{func.__name__}': Array variables cannot have parameters."
            raise CashflowModelError(msg)

        # Create a variable
        if array:
            v = ArrayVariable(func)
        elif func.__code__.co_argcount == 0:
            v = ConstantVariable(func)
        else:
            v = Variable(func)

        return v
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
        # In cycle, the calculation order might not be known
        if self.cycle and (t is not None and t not in self.cycle_cache):
            self.cycle_cache.add(t)
            self.result[t] = self.func(t)

        if t is None:
            return self.result
        else:
            try:
                return self.result[t]
            except IndexError as e:
                if t > self.t_max:
                    msg = (f"Variable '{self.name}' has been called for period '{t}' "
                           f"which is outside of the calculation range.")
                    raise CashflowModelError(msg)
                else:
                    print(str(e))

    @property
    def t_max(self):
        return self._t_max

    @t_max.setter
    def t_max(self, new_t_max):
        self._t_max = new_t_max
        self.result = np.empty(self.t_max + 1)

    def calculate_t(self, t):
        # This method is used for cycles only
        if t not in self.cycle_cache:
            self.cycle_cache.add(t)
            self.result[t] = self.func(t)

    def calculate(self):
        if self.calc_direction == 0:
            self.result = np.array([*map(self.func, range(self.t_max + 1))], dtype=np.float64)
        elif self.calc_direction == 1:
            for t in range(self.t_max + 1):
                self.result[t] = self.func(t)
        elif self.calc_direction == -1:
            for t in range(self.t_max, -1, -1):
                self.result[t] = self.func(t)
        else:
            raise CashflowModelError(f"Incorrect calculation direction {self.calc_direction}")


class ConstantVariable(Variable):
    """Variable that is constant in time."""
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
        self.result = np.array([value for _ in range(0, self.t_max + 1)], dtype=np.float64)


class ArrayVariable(Variable):
    """Variable that returns an array."""
    def __init__(self, func):
        Variable.__init__(self, func)

    def __repr__(self):
        return f"AV: {self.func.__name__}"

    def __call__(self, t=None):
        if t is None:
            return self.result
        else:
            return self.result[t]

    def calculate(self):
        self.result = np.array(self.func(), dtype=np.float64)


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

    @functools.lru_cache()
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
    def __init__(self, variables, model_point_sets, settings):
        self.variables = variables
        self.model_point_sets = model_point_sets
        self.settings = settings

    def run(self, part=None):
        """Orchestrate all steps of the cash flow model run."""
        one_core = part == 0 or part is None  # single or first part
        main = get_object_by_name(self.model_point_sets, "main")

        # Set calculation ranges
        range_start, range_end = 0, len(main)
        if self.settings["MULTIPROCESSING"]:
            main_ranges = split_to_ranges(len(main), multiprocessing.cpu_count())
            # Number of model points is lower than the number of cpus, only calculate on the 1st core
            if part >= len(main_ranges):
                return None
            range_start, range_end = main_ranges[part]

        # Create partial calculation function for map
        progressbar_max = len(main) if range_end is None else range_end

        # Perform calculations
        print_log("Starting calculations...", visible=one_core)
        if self.settings["AGGREGATE"]:
            results = self.compute_aggregated_results(range_start, range_end, one_core, progressbar_max)
        else:
            results = self.compute_individual_results(range_start, range_end, one_core, progressbar_max)

        # Prepare the 'output' data frame
        print_log("Preparing output...", visible=one_core)
        if len(self.settings["OUTPUT_COLUMNS"]) == 0:
            output_columns = [v.name for v in self.variables]
        else:
            output_columns = self.settings["OUTPUT_COLUMNS"]

        if self.settings["AGGREGATE"]:
            output = pd.DataFrame(data=results, columns=output_columns)
        else:
            total_data = [pd.DataFrame(np.transpose(arr)) for arr in results]
            output = pd.concat(total_data, axis=0)
            output.columns = output_columns

        # Get diagnostic file
        diagnostic = None
        if self.settings["SAVE_DIAGNOSTIC"]:
            diagnostic = pd.DataFrame({
                "variable": [v.name for v in self.variables],
                "calc_order": [v.calc_order for v in self.variables],
                "cycle": [v.cycle for v in self.variables],
                "calc_direction": [v.calc_direction for v in self.variables],
                "type": [get_variable_type(v) for v in self.variables],
                "runtime": [v.runtime for v in self.variables]
            })

        return output, diagnostic

    def compute_aggregated_results(self, range_start, range_end, one_core, progressbar_max):
        results = None
        p = functools.partial(self.calculate_model_point, one_core=one_core, progressbar_max=progressbar_max)

        # Calculate batch_size based on available memory
        t = self.settings["T_MAX_OUTPUT"] + 1
        v = len(self.variables) if len(self.settings["OUTPUT_COLUMNS"]) == 0 else len(self.settings["OUTPUT_COLUMNS"])
        float_size = np.dtype(np.float64).itemsize
        num_cores = 1 if not self.settings["MULTIPROCESSING"] else multiprocessing.cpu_count()
        batch_size = int((psutil.virtual_memory().available * 0.95) // ((t * v) * float_size) // num_cores)

        # Calculate batches iteratively
        batch_start, batch_end = range_start, min(range_start + batch_size, range_end)
        first = True
        while batch_start < range_end:
            lst = [*map(p, range(batch_start, batch_end))]
            if first:
                results = functools.reduce(lambda a, b: a + b, lst)
                first = False
            else:
                results += functools.reduce(lambda a, b: a + b, lst)

            batch_start = batch_end
            batch_end = min(batch_end+batch_size, range_end)

        results = np.transpose(results)
        return results

    def compute_individual_results(self, range_start, range_end, one_core, progressbar_max):
        p = functools.partial(self.calculate_model_point, one_core=one_core, progressbar_max=progressbar_max)

        # Allocate memory for results
        t = self.settings["T_MAX_OUTPUT"] + 1
        v = len(self.variables) if len(self.settings["OUTPUT_COLUMNS"]) == 0 else len(self.settings["OUTPUT_COLUMNS"])
        mp = range_end - range_start
        float_size = np.dtype(np.float64).itemsize
        results_size = t * v * mp * float_size
        results_size_mb = results_size / (1024 ** 2)
        num_cores = 1 if not self.settings["MULTIPROCESSING"] else multiprocessing.cpu_count()

        # Results may require a lot of memory
        msg = (f"Failed to allocate memory for the output with {t} periods, {v} variables, and {mp} model points "
               f"(~{results_size_mb:.0f}) MB. Terminating model execution.")

        # Results do not fit into total RAM memory
        total_ram_memory = psutil.virtual_memory().total / num_cores
        if results_size > total_ram_memory:
            raise CashflowModelError(msg)

        # Allocate results to available RAM memory
        try:
            results = [np.empty((v, t), dtype=float) for _ in range(mp)]
        except MemoryError:
            raise CashflowModelError(msg)
        else:
            results = [*map(p, range(range_start, range_end))]

        return results

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
            variables = [v for v in self.variables if v.calc_order == calc_order]
            # Single
            if len(variables) == 1:
                v = variables[0]
                start = time.time()
                v.calculate()
                v.runtime += time.time() - start
            # Cycle
            else:
                start = time.time()
                first_variable = variables[0]
                calc_direction = first_variable.calc_direction
                if calc_direction in (0, 1):
                    for t in range(self.settings["T_MAX_CALCULATION"] + 1):
                        for v in variables:
                            v.calculate_t(t)
                else:
                    for t in range(self.settings["T_MAX_CALCULATION"], -1, -1):
                        for v in variables:
                            v.calculate_t(t)
                end = time.time()
                avg_runtime = (end-start)/len(variables)
                for v in variables:
                    v.runtime += avg_runtime

        # Clear cache of cycle variables
        for v in self.variables:
            if v.cycle:
                v.cycle_cache.clear()

        # Get results and trim for T_MAX_OUTPUT,results may contain subset of columns
        if len(self.settings["OUTPUT_COLUMNS"]) > 0:
            mp_results = np.array([v.result[:self.settings["T_MAX_OUTPUT"]+1] for v in self.variables if v.name in self.settings["OUTPUT_COLUMNS"]])
        else:
            mp_results = np.array([v.result[:self.settings["T_MAX_OUTPUT"]+1] for v in self.variables])

        # Update progressbar
        if one_core:
            updt(progressbar_max, row + 1)

        return mp_results