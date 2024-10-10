import functools
import time
import multiprocessing
import numpy as np
import pandas as pd
import psutil

from .error import CashflowModelError
from .utils import get_first_indexes, get_object_by_name, log_message, split_to_ranges, update_progressbar


def get_variable_type(v):
    """
    Returns the type of the given variable.

    Args:
        v (object): The variable to check.

    Returns:
        str: The type of the variable. Possible values are "constant", "array", "stochastic", and "default".
    """
    if isinstance(v, ConstantVariable):
        return "constant"
    elif isinstance(v, ArrayVariable):
        return "array"
    elif isinstance(v, StochasticVariable):
        return "stochastic"
    else:
        return "default"


def check_arguments(func, array):
    """
    Check if the input function has the correct arguments.

    The function should have at most two parameters, 't' and 'stoch'. If the function has two parameters,
    the first one should be named 't' and the second one should be named 'stoch'.
    If the function has only one parameter, it should be named 't'. Additionally, if the input 'array' is True,
    the function should not have any parameters.

    Parameters:
        func (function): The function to check.
        array (bool): Whether the function is an array variable.

    Raises:
        CashflowModelError: If the function does not meet the required criteria.
    """
    # Variable has at most 2 parameters ("t" and "stoch")
    if func.__code__.co_argcount > 2:
        msg = f"Error in '{func.__name__}': The model variable should have at most two parameters ('t' and 'stoch')."
        raise CashflowModelError(msg)

    # The first parameter must be named "t" and second "stoch"
    if func.__code__.co_argcount == 2:
        if not func.__code__.co_varnames[0] == 't':
            msg = f"Error in '{func.__name__}': The first parameter should be named 't'."
            raise CashflowModelError(msg)

        if not func.__code__.co_varnames[1] == 'stoch':
            msg = f"Error in '{func.__name__}': The second parameter should be named 'stoch'."
            raise CashflowModelError(msg)

    # The only parameter must be named "t"
    if func.__code__.co_argcount == 1:
        if not func.__code__.co_varnames[0] == 't':
            msg = f"Error in '{func.__name__}': The parameter should be named 't'."
            raise CashflowModelError(msg)

    # Array variables should not have any parameters
    if array and not func.__code__.co_argcount == 0:
        msg = f"Error in '{func.__name__}': Array variables cannot have parameters."
        raise CashflowModelError(msg)

    return None


def variable(array=False, aggregation_type="sum"):
    """A decorator that transforms a function into an object of class Variable."""
    def wrapper(func):
        check_arguments(func, array)

        # Create a variable
        if array:
            v = ArrayVariable(func, aggregation_type)
        elif func.__code__.co_argcount == 0:
            v = ConstantVariable(func, aggregation_type)
        elif func.__code__.co_argcount == 2:
            v = StochasticVariable(func, aggregation_type)
        else:
            v = Variable(func, aggregation_type)

        return v
    return wrapper


class Variable:
    """
    Represents a variable in a cashflow model.

    @variable()
    def my_var(t):
        ...

    Attributes:
        func (function): The function that calculates the variable's value.
        aggregation_type (str): The type of aggregation to apply to the variable's values.
        name (str): The name of the variable.
        calc_direction (int): The direction of calculation (0: normal, 1: forward, -1: backward).
        calc_order (int): The order in which the variable is calculated.
        cycle (bool): Whether the variable is part of a cycle.
        cycle_order (int): The order of the variable in its cycle.
        result (list): The calculated values of the variable.
        runtime (float): The time it took to calculate the variable's values.
    """
    def __init__(self, func, aggregation_type):
        self.func = func
        self.aggregation_type = aggregation_type
        self.name = None
        self.calc_direction = None
        self.calc_order = None
        self.cycle = False
        self.cycle_order = 0
        self.result = None
        self.runtime = 0.0

    def __repr__(self):
        return f"V: {self.func.__name__}"

    def __lt__(self, other):
        return self.name < other.name

    def __call__(self, t=None):
        if t is None:
            return self.result

        # Python allows negative indexing, which would wrap around to the end of the list.
        # To prevent this and ensure t is within the valid range, we explicitly check for t < 0.
        if t < 0:
            msg = (f"\n\nVariable '{self.name}' has been called for period '{t}' "
                   f"which is outside of the calculation range.")
            raise CashflowModelError(msg)

        # Easier to ask forgiveness
        try:
            return self.result[t]
        except IndexError as e:
            if t > len(self.result):
                msg = (f"\n\nVariable '{self.name}' has been called for period '{t}' "
                       f"which is outside of the calculation range.")
                raise CashflowModelError(msg)
            else:
                print(str(e))

    def calculate_t(self, t):
        """For cycle calculations"""
        self.result[t] = self.func(t)

    def calculate(self):
        t_max = len(self.result)
        if self.calc_direction == 0:
            self.result = np.array([self.func(t) for t in range(t_max)], dtype=np.float64)
        elif self.calc_direction == 1:
            for t in range(t_max):
                self.result[t] = self.func(t)
        elif self.calc_direction == -1:
            for t in range(t_max-1, -1, -1):
                self.result[t] = self.func(t)
        else:
            raise CashflowModelError(f"\n\nIncorrect calculation direction '{self.calc_direction}'.")


class ConstantVariable(Variable):
    """Variable that is constant in time.

    @variable()
    def my_var():
        ...
    """
    def __init__(self, func, aggregation_type):
        Variable.__init__(self, func, aggregation_type)

    def __repr__(self):
        return f"CV: {self.func.__name__}"

    def __call__(self, t=None):
        return self.result[0]

    def calculate_t(self, t):
        """For cycle calculations"""
        self.result[t] = self.func()

    def calculate(self):
        value = self.func()
        self.result.fill(value)


class ArrayVariable(Variable):
    """Variable that returns an array (for runtime improvements).

    @variable(array=True)
    def my_var():
        ...
    """
    def __init__(self, func, aggregation_type):
        Variable.__init__(self, func, aggregation_type)

    def __repr__(self):
        return f"AV: {self.func.__name__}"

    def calculate(self):
        self.result = np.array(self.func(), dtype=np.float64)


class StochasticVariable(Variable):
    """Stochastic variable.

    @variable()
    def my_var(t, stoch):
        ...
    """
    def __init__(self, func, aggregation_type):
        Variable.__init__(self, func, aggregation_type)
        self.result_stoch = None

    def __repr__(self):
        return f"SV: {self.func.__name__}"

    def __call__(self, t, stoch):
        return self.result_stoch[stoch-1, t]

    def calculate_t(self, t):
        """For cycle calculations"""
        stoch_scenarios_count = self.result_stoch.shape[0]
        stoch_range = np.arange(1, stoch_scenarios_count + 1)
        self.result_stoch[:, t] = self.func(t, stoch_range)

    def calculate(self):
        stoch_scenarios_count, t_max = self.result_stoch.shape

        if self.calc_direction == 0:
            for stoch in range(1, stoch_scenarios_count + 1):
                func_with_stoch = functools.partial(self.func, stoch=stoch)
                self.result_stoch[stoch-1, :] = np.array([func_with_stoch(t) for t in range(t_max)], dtype=np.float64)
        elif self.calc_direction == 1:
            for t in range(t_max):
                self.result_stoch[:, t] = [self.func(t, stoch) for stoch in range(1, stoch_scenarios_count + 1)]
        elif self.calc_direction == -1:
            for t in range(t_max-1, -1, -1):
                self.result_stoch[:, t] = [self.func(t, stoch) for stoch in range(1, stoch_scenarios_count + 1)]
        else:
            raise CashflowModelError(f"\n\nIncorrect calculation direction '{self.calc_direction}'.")

    def average_result_stoch(self):
        self.result = np.mean(self.result_stoch, axis=0)


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
        # Converts the 'version' column to string and sets it as the index,
        # while keeping the original 'version' column intact.
        self.data = self.data.set_index(self.data["version"].astype(str))

        # Set version (first one if not chosen by the user)
        if version is None:
            self.version = str(self.data["version"].iloc[0])
        else:
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

    def initialize(self):
        """Additional initialization (beyond __init__) is required
        since 'name' and 'settings' are not available during object creation."""
        self.perform_checks()
        self.set_index()
        self.id = self.data.iloc[0][self.settings["ID_COLUMN"]]

    @functools.lru_cache()
    def get(self, attribute, record_num=0):
        # Note: Only the 'main' model point set is guaranteed to have all IDs;
        # other model point sets may not have rows for every ID
        if self.id is None:
            return None

        return self.model_point_data.iloc[record_num][attribute]

    @property
    def id(self):
        """Get the current model point's ID."""
        return self._id

    @id.setter
    def id(self, new_id):
        """Set the model point's ID and update corresponding attributes."""
        new_id = str(new_id)
        if new_id in self.data.index:
            self._id = new_id
            self.model_point_data = self.data.loc[[new_id]]
        else:
            self._id = None
        self.get.cache_clear()

    def set_id(self, new_id):
        self.id = new_id

    def perform_checks(self):
        id_column_name = self.settings["ID_COLUMN"]

        # Model point set must have ID_COLUMN
        if id_column_name not in self.data.columns:
            raise CashflowModelError(f"\nModel point set '{self.name}' is missing the required column '{id_column_name}'.")

        # ID must be unique in the 'main' model point set
        if self.name == "main":
            if not self.data[id_column_name].is_unique:
                raise CashflowModelError(f"\nThe 'main' model point set must have unique values in '{id_column_name}' column.")

    def set_index(self):
        """Convert ID column to string and use it as index, while preserving the original ID column."""
        id_column_name = self.settings["ID_COLUMN"]
        self.data = self.data.set_index(self.data[id_column_name].astype(str))


class Model:
    """Actuarial cash flow model.
    Model combines model variables and model point sets."""
    def __init__(self, variables, model_point_sets, settings):
        self.variables = variables
        self.model_point_sets = model_point_sets
        self.settings = settings

    def run(self, part=None):
        """Orchestrate all steps of the cash flow model run."""
        # Get model point indices (full for single core; split for multiprocessing)
        calculation_range = self.get_calculation_range(part)
        if calculation_range is None:  # less model points than CPUs
            return None
        range_start, range_end = calculation_range

        # User can choose output columns
        output_columns = self.get_output_columns()

        # Perform calculations
        one_core = part == 0 or part is None  # bool; single core or first part of multiprocessing calculation
        log_message("Starting calculations...", show_time=True, print_and_save=one_core)
        group_sums = self.perform_calculations(range_start, range_end, one_core, output_columns)

        # Transform results into a data frame
        output = self.prepare_output(group_sums, output_columns, one_core)

        # Create a diagnostic file
        diagnostic = self.create_diagnostic_data()

        return output, diagnostic

    def get_calculation_range(self, part):
        main = get_object_by_name(self.model_point_sets, "main")
        range_start, range_end = 0, len(main)
        if self.settings["MULTIPROCESSING"]:
            main_ranges = split_to_ranges(len(main), multiprocessing.cpu_count())
            # Number of model points is lower than the number of CPUs, only calculate on the 1st core
            if part >= len(main_ranges):
                return None
            range_start, range_end = main_ranges[part]
        return range_start, range_end

    def get_output_columns(self):
        if len(self.settings["OUTPUT_COLUMNS"]) == 0:
            output_columns = [v.name for v in self.variables]
        else:
            output_columns = self.settings["OUTPUT_COLUMNS"]
        return output_columns

    def allocate_memory_for_output(self, mp):
        t = self.settings["T_MAX_OUTPUT"] + 1
        v = len(self.variables) if len(self.settings["OUTPUT_COLUMNS"]) == 0 else len(self.settings["OUTPUT_COLUMNS"])

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

        return results

    def perform_calculations(self, range_start, range_end, one_core, output_columns):
        max_output = self.settings["T_MAX_OUTPUT"] + 1
        group_by = self.settings["GROUP_BY"]
        main = get_object_by_name(self.model_point_sets, "main")
        calculate_model_point_partial = functools.partial(
            self.calculate_model_point, one_core=one_core, progressbar_max=range_end
        )
        num_output_columns = len(output_columns)

        # Define the initial batch size to process, to prevent excessive memory usage
        batch_size = self.get_batch_size(num_output_columns)
        batch_start, batch_end = range_start, min(range_start + batch_size, range_end)

        # Create an array of multipliers based on the aggregation type of each variable
        output_variables = [get_object_by_name(self.variables, column) for column in output_columns]
        multiplier = np.array([1 if v.aggregation_type == "sum" else 0 for v in output_variables])

        # Grouping column must be part of the model point set
        if group_by and group_by not in main.data.columns:
            msg = (f"There is no column '{group_by}' in the 'main' model point set. "
                   f"Please review the 'GROUP_BY' setting.")
            raise CashflowModelError(msg)

        # Handle grouping if group_by is set, otherwise treat everything as a single group
        unique_groups = main.data[group_by].unique() if group_by else [None]
        group_sums = {group: np.zeros((max_output, num_output_columns)) for group in unique_groups}

        # Get first indexes of groups
        first_indexes = get_first_indexes(main.data[group_by]) if group_by else []

        # Populate results for the first model point (needed for aggregation_type=first)
        if batch_start == 0:
            first_group = main.data.iloc[0][group_by] if group_by else None
            group_sums[first_group] = calculate_model_point_partial(0)
            batch_start += 1

        # Process batches iteratively to calculate the results
        # batch_results_list is a list of model point results (each result is a 2D array)
        while batch_start < range_end:
            batch_results_list = [calculate_model_point_partial(i) for i in range(batch_start, batch_end)]
            batch_range = batch_end - batch_start
            groups = main.data.iloc[batch_start:batch_end][group_by].tolist() if group_by else [None] * batch_range
            if_firsts = np.isin(range(batch_start, batch_end), first_indexes)

            # When aggregation_type=first, we want results only once
            for mp_result, group, if_first in zip(batch_results_list, groups, if_firsts):
                if if_first:
                    group_sums[group] += mp_result
                else:
                    group_sums[group] += mp_result * multiplier[None, :]

            batch_start = batch_end
            batch_end = min(batch_end + batch_size, range_end)

        return group_sums

    def get_batch_size(self, num_output_columns):
        """
        Calculate the batch size based on available memory.

        The batch size is calculated to avoid memory errors when processing model points.
        Each model point outputs a numpy array with "t" rows and "num_output_columns" columns.
        The calculation takes into account whether the processing is done on one core or multiple cores (multiprocessing).

        Args:
            num_output_columns (int): The number of output columns.

        Returns:
            int: The number of model points to be processed.
        """
        t = self.settings["T_MAX_OUTPUT"] + 1
        float_size = np.dtype(np.float64).itemsize
        num_cores = 1 if not self.settings["MULTIPROCESSING"] else multiprocessing.cpu_count()
        available_memory = psutil.virtual_memory().available * 0.95
        memory_per_model_point = (t * num_output_columns) * float_size
        batch_size = int(available_memory // (memory_per_model_point // num_cores))
        batch_size = max(batch_size, 1)
        return batch_size

    def prepare_output(self, group_sums, output_columns, one_core):
        group_by = self.settings["GROUP_BY"]
        log_message("Preparing output...", show_time=True, print_and_save=one_core)

        lst_dfs = []
        for group, data in group_sums.items():
            group_df = pd.DataFrame(data=data, columns=output_columns)
            if group_by:
                group_df.insert(0, group_by, group)
            lst_dfs.append(group_df)

        output = pd.concat(lst_dfs, ignore_index=True)
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
            model_point_set.set_id(model_point_id)

        # Perform calculations
        max_calc_order = self.variables[-1].calc_order
        for calc_order in range(1, max_calc_order + 1):
            # Either a single variable or a cycle
            variables = [v for v in self.variables if v.calc_order == calc_order]

            # Single variable
            if len(variables) == 1:
                v = variables[0]
                start = time.time()
                v.calculate()
                v.runtime += time.time() - start
            # Cycle
            else:
                self.calculate_cycle(variables)

        # Average stochastic results
        for v in self.variables:
            if isinstance(v, StochasticVariable):
                v.average_result_stoch()

        # Get results and trim for T_MAX_OUTPUT (results may contain subset of columns)
        if len(self.settings["OUTPUT_COLUMNS"]) > 0:
            mp_results = np.array([v.result[:self.settings["T_MAX_OUTPUT"]+1] for v in self.variables if v.name in self.settings["OUTPUT_COLUMNS"]])
        else:
            mp_results = np.array([v.result[:self.settings["T_MAX_OUTPUT"]+1] for v in self.variables])

        # Transpose the matrix
        mp_results = mp_results.T

        # Update progressbar
        if one_core:
            update_progressbar(progressbar_max, row + 1)

        return mp_results

    def calculate_cycle(self, variables):
        start = time.time()
        first_variable = variables[0]
        calc_direction = first_variable.calc_direction
        t_max_calculation = self.settings["T_MAX_CALCULATION"]

        if calc_direction in (0, 1):
            for t in range(t_max_calculation + 1):
                for v in variables:
                    v.calculate_t(t)
        else:
            for t in range(t_max_calculation, -1, -1):
                for v in variables:
                    v.calculate_t(t)

        end = time.time()
        avg_runtime = (end-start)/len(variables)
        for v in variables:
            v.runtime += avg_runtime

    def create_diagnostic_data(self):
        if self.settings["SAVE_DIAGNOSTIC"]:
            diagnostic = pd.DataFrame({
                "variable": [v.name for v in self.variables],
                "calc_order": [v.calc_order for v in self.variables],
                "calc_direction": [v.calc_direction for v in self.variables],
                "cycle": [v.cycle for v in self.variables],
                "cycle_order": [v.cycle_order for v in self.variables],
                "variable_type": [get_variable_type(v) for v in self.variables],
                "aggregation_type": [v.aggregation_type for v in self.variables],
                "runtime": [v.runtime for v in self.variables]
            })
        else:
            diagnostic = None

        return diagnostic
