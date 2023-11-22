import functools
import time
import multiprocessing
import numpy as np
import pandas as pd
import psutil

from .error import CashflowModelError
from .utils import get_first_indexes, get_object_by_name, print_log, split_to_ranges, updt


def get_variable_type(v):
    if isinstance(v, ConstantVariable):
        return "constant"
    elif isinstance(v, ArrayVariable):
        return "array"
    else:
        return "default"


def variable(array=False, aggregation_type="sum"):
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
            v = ArrayVariable(func, aggregation_type)
        elif func.__code__.co_argcount == 0:
            v = ConstantVariable(func, aggregation_type)
        else:
            v = Variable(func, aggregation_type)

        return v
    return wrapper


class Variable:
    def __init__(self, func, aggregation_type):
        self.func = func
        self.aggregation_type = aggregation_type
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
    def __init__(self, func, aggregation_type):
        Variable.__init__(self, func, aggregation_type)

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
    def __init__(self, func, aggregation_type):
        Variable.__init__(self, func, aggregation_type)

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
    """Runplan of the cash flow model.

    Runplan allows to run the model with different parameters. It is defined in the 'input.py' script.

    The version can be defined either:
    - during definition of the object in the 'input.py' script,
    - with command-line arguments (for example: "python run.py --version 3").
    """
    def __init__(self, data, version=None):
        self.data = data
        self.perform_checks()
        self.set_index(version)

    @functools.lru_cache()
    def get(self, attribute):
        """Get a value from the runplan for the current version."""
        return self.data.at[self.version, attribute]

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, new_version):
        if new_version is not None:
            new_version = str(new_version)
            if new_version not in self.data.index:
                raise CashflowModelError(f"There is no version '{new_version}' in the runplan.")
            self._version = new_version

    def perform_checks(self):
        # Runplan must have a "version" column
        if "version" not in self.data.columns:
            raise CashflowModelError("Runplan must have the 'version' column.")

        # Version must be unique
        if not self.data["version"].is_unique:
            msg = "Runplan must have unique values in the 'version' column."
            raise CashflowModelError(msg)

    def set_index(self, version):
        """Version in original form stays as a column, version as a string becomes an index."""
        self.data["version_duplicate"] = self.data["version"]
        self.data["version"] = self.data["version"].astype(str)
        self.data = self.data.set_index("version")
        self.data["version"] = self.data["version_duplicate"]
        self.data = self.data.drop(columns=["version_duplicate"])
        if version is None:  # user has not specified version
            self.version = str(self.data["version"].iloc[0])
        else:  # user has specified version
            self.version = str(version)


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
        # Model point sets other than main may not have rows for all IDs
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
        new_id = str(new_id)
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
        # Model point set must have id_column
        id_column = self.settings["ID_COLUMN"]
        if id_column not in self.data.columns:
            raise CashflowModelError(f"\nThere is no column '{id_column}' in model_point_set '{self.name}'.")

        # ID must be unique in the 'main' model point set
        id_column = self.settings["ID_COLUMN"]
        if self.name == "main":
            if not self.data[id_column].is_unique:
                msg = f"\nThe 'main' model point set must have unique values in '{id_column}' column."
                raise CashflowModelError(msg)

    def set_index(self):
        """ID column in original form stays as a column, ID column as a string becomes an index."""
        id_column = self.settings["ID_COLUMN"]
        self.data[id_column + "_duplicate"] = self.data[id_column]
        self.data[id_column] = self.data[id_column].astype(str)
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
            # Number of model points is lower than the number of CPUs, only calculate on the 1st core
            if part >= len(main_ranges):
                return None
            range_start, range_end = main_ranges[part]

        # Perform calculations
        print_log("Starting calculations...", show_time=True, visible=one_core)
        if self.settings["AGGREGATE"]:
            output = self.compute_aggregated_results(range_start, range_end, one_core)
        else:
            output = self.compute_individual_results(range_start, range_end, one_core)

        # Create a diagnostic file
        diagnostic = None
        if self.settings["SAVE_DIAGNOSTIC"]:
            diagnostic = pd.DataFrame({
                "variable": [v.name for v in self.variables],
                "calc_order": [v.calc_order for v in self.variables],
                "cycle": [v.cycle for v in self.variables],
                "calc_direction": [v.calc_direction for v in self.variables],
                "variable_type": [get_variable_type(v) for v in self.variables],
                "aggregation_type": [v.aggregation_type for v in self.variables],
                "runtime": [v.runtime for v in self.variables]
            })

        return output, diagnostic

    def compute_aggregated_results(self, range_start, range_end, one_core):
        p = functools.partial(self.calculate_model_point, one_core=one_core, progressbar_max=range_end)

        # Multiplier that takes into account aggregation type
        multiplier = np.array([1 if v.aggregation_type == "sum" else 0 for v in self.variables])

        # Prepare output columns
        if len(self.settings["OUTPUT_COLUMNS"]) == 0:
            output_columns = [v.name for v in self.variables]
        else:
            output_columns = self.settings["OUTPUT_COLUMNS"]

        # Calculate batch_size based on available memory
        t = self.settings["T_MAX_OUTPUT"] + 1
        v = len(output_columns)
        float_size = np.dtype(np.float64).itemsize
        num_cores = 1 if not self.settings["MULTIPROCESSING"] else multiprocessing.cpu_count()
        batch_size = int((psutil.virtual_memory().available * 0.95) // ((t * v) * float_size) // num_cores)

        # Initial calculation batch
        batch_start, batch_end = range_start, min(range_start + batch_size, range_end)

        # Aggregate all model points (without grouping)
        if self.settings["GROUP_BY_COLUMN"] is None:
            # Initiate with results of the first model point
            if batch_start == 0:
                results = p(0)
                batch_start += 1
            else:
                results = 0

            # Calculate batches iteratively
            while batch_start < range_end:
                lst = [*map(p, range(batch_start, batch_end))]  # list of mp_results (arrays of arrays)
                batch_results = functools.reduce(lambda a, b: a + b, lst)
                results += batch_results * multiplier[:, None]
                batch_start = batch_end
                batch_end = min(batch_end+batch_size, range_end)

            # Prepare the 'output' data frame
            print_log("Preparing output...", show_time=True, visible=one_core)
            results = np.transpose(results)
            output = pd.DataFrame(data=results, columns=output_columns)

        # Aggregate by groups
        else:
            main = get_object_by_name(self.model_point_sets, "main")
            group_by_column = self.settings["GROUP_BY_COLUMN"]
            if group_by_column not in main.data.columns:
                msg = (f"There is no column '{group_by_column}' in the 'main' model point set. "
                       f"Please review the 'GROUP_BY_COLUMN' setting.")
                raise CashflowModelError(msg)
            unique_groups = main.data[group_by_column].unique()

            # Indexes of the first element from each group
            first_indexes = get_first_indexes(main.data[group_by_column])

            # Initiate empty results
            group_sums = {group: np.array([np.zeros(t) for _ in range(v)]) for group in unique_groups}

            # Calculate batches iteratively
            while batch_start < range_end:
                lst = [*map(p, range(batch_start, batch_end))]  # list of mp_results
                groups = main.data.iloc[batch_start:batch_end][group_by_column].tolist()
                if_firsts = [i in first_indexes for i in range(batch_start, batch_end)]

                for mp_result, group, if_first in zip(lst, groups, if_firsts):
                    if if_first:
                        group_sums[group] += mp_result
                    else:
                        group_sums[group] += mp_result * multiplier[:, None]
                batch_start = batch_end
                batch_end = min(batch_end+batch_size, range_end)

            # Prepare the 'output' data frame
            print_log("Preparing output...", show_time=True, visible=one_core)
            lst_dfs = []
            for group, data in group_sums.items():
                group_df = pd.DataFrame(data=np.transpose(data), columns=output_columns)
                group_df.insert(0, group_by_column, group)
                lst_dfs.append(group_df)
            output = pd.concat(lst_dfs, ignore_index=True)

        return output

    def compute_individual_results(self, range_start, range_end, one_core):
        p = functools.partial(self.calculate_model_point, one_core=one_core, progressbar_max=range_end)

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

        # Prepare output columns
        if len(self.settings["OUTPUT_COLUMNS"]) == 0:
            output_columns = [v.name for v in self.variables]
        else:
            output_columns = self.settings["OUTPUT_COLUMNS"]

        # Prepare the 'output' data frame
        print_log("Preparing output...", show_time=True, visible=one_core)
        total_data = [pd.DataFrame(np.transpose(arr)) for arr in results]
        output = pd.concat(total_data)
        output.columns = output_columns

        return output

    def calculate_model_point(self, row, one_core, progressbar_max):
        """Returns array of arrays:
        [[v1_t0, v1_t1, v1_t2, ... v1_tm],
         [v2_t0, v2_t1, v2_t2, ... v2_tm],
         ...
         [vn_t0, vn_t1, vn_t2, ... v2_tm]]"""
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
