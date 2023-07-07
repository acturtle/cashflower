import functools
import itertools
import networkx as nx
import time
import pandas as pd

from .error import CashflowModelError
from .utils import get_object_by_name, print_log, split_to_ranges, updt
from .graph import get_calc_direction, get_calls, get_predecessors


def variable():
    """Decorator"""
    def wrapper(func):
        variable = Variable(func)
        return variable
    return wrapper


class Variable:
    def __init__(self, func):
        self.func = func
        self.name = None
        self._settings = None
        self.result = None
        self.calls = None
        self.calc_order = None
        self.cycle = False
        self.calc_direction = None
        self.runtime = 0

    def __repr__(self):
        return f"V: {self.func.__name__}"

    def __call__(self, t):
        if t < 0 or t > self.settings["T_MAX_CALCULATION"]:
            msg = f"Variable '{self.name}' has been called for period '{t}' which is outside of calculation range."
            raise CashflowModelError(msg)

        # In the cycle, we don't know exact calculation order
        if self.cycle and self.result[t] is None:
            return self.func(t)

        if self.result[t] is None:
            msg = f"Variable '{self.name}' has been called for period '{t}' which hasn't been calculated yet."
            raise CashflowModelError(msg)

        return self.result[t]

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, new_settings):
        self._settings = new_settings
        self.result = [None for _ in range(0, self.settings["T_MAX_CALCULATION"] + 1)]

    def calculate_t(self, t):
        self.result[t] = self.func(t)

    def calculate_forward(self):
        for t in range(self.settings["T_MAX_CALCULATION"] + 1):
            self.result[t] = self.func(t)

    def calculate_backward(self):
        for t in range(self.settings["T_MAX_CALCULATION"], -1, -1):
            self.result[t] = self.func(t)

    def calculate(self):
        if self.calc_direction == "irrelevant":
            self.result = [*map(self.func, range(self.settings["T_MAX_CALCULATION"] + 1))]
        elif self.calc_direction == "forward":
            self.calculate_forward()
        elif self.calc_direction == "backward":
            self.calculate_backward()
        else:
            raise CashflowModelError(f"Incorrect calculation direction {self.calc_direction}")


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

    def get(self, attribute, record_num=0):
        return self.model_point_data.iloc[record_num][attribute]

    @property
    def id(self):
        """Current model point's id."""
        return self._id

    @id.setter
    def id(self, new_id):
        """Set model point's id and corresponding attributes."""
        self._id = new_id

        if new_id not in self.data.index:
            raise CashflowModelError(f"There is no id '{new_id}' in model_point_set '{self.name}'.")

        self.model_point_data = self.data.loc[[new_id]]

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

        # Get variables' calls
        for variable in self.variables:
            variable.calls = get_calls(variable, self.variables)

        # Create directed graph for all variables
        DG = nx.DiGraph()
        for variable in self.variables:
            DG.add_node(variable)
            for predecessor in variable.calls:
                DG.add_edge(predecessor, variable)

        # Draw graph
        # nx.draw(DG, with_labels=True, font_weight='bold')
        # plt.show()

        # Set calc_order in variables
        calc_order = 0
        while DG.nodes:
            nodes_without_predecessors = [node for node in DG.nodes if len(list(DG.predecessors(node))) == 0]
            if len(nodes_without_predecessors) > 0:
                for node in nodes_without_predecessors:
                    calc_order += 1
                    node.calc_order = calc_order
                DG.remove_nodes_from(nodes_without_predecessors)
            else:  # it's a cycle
                cycles = list(nx.simple_cycles(DG))
                cycles_without_predecessors = [c for c in cycles if len(get_predecessors(c[0], DG)) == len(c)]

                if len(cycles_without_predecessors) == 0:
                    big_cycle = list(set(list(itertools.chain(*cycles))))
                    cycles_without_predecessors = [big_cycle]

                for cycle_without_predecessors in cycles_without_predecessors:
                    calc_order += 1
                    for node in cycle_without_predecessors:
                        node.calc_order = calc_order
                        node.cycle = True
                    DG.remove_nodes_from(cycle_without_predecessors)

        # Sort variables for calculation order
        self.variables = sorted(self.variables, key=lambda x: (x.calc_order, x.name))

        # Get calc_direction of calculation
        max_calc_order = self.variables[-1].calc_order
        for calc_order in range(1, max_calc_order+1):
            # Either a single variable or a cycle
            variables = [variable for variable in self.variables if variable.calc_order == calc_order]
            get_calc_direction(variables)

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
        if self.settings["AGGREGATE"] is False:
            result = pd.concat(results)
        else:
            result = functools.reduce(lambda x, y: x.add(y, fill_value=0), results)

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
                if calc_direction in ("irrelevant", "forward"):
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

        # Get results and trim for T_MAX_OUTPUT
        columns = [variable.name for variable in self.variables]
        data = [variable.result[:self.settings["T_MAX_OUTPUT"]+1] for variable in self.variables]
        data = map(list, zip(*data))  # transpose
        data_frame = pd.DataFrame(data, columns=columns)

        # Results may contain subset of columns
        if len(self.settings["OUTPUT_COLUMNS"]) > 0:
            data_frame = data_frame[self.settings["OUTPUT_COLUMNS"]]

        # Update progessbar
        if one_core:
            updt(progressbar_max, row + 1)

        return data_frame
