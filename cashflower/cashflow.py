import functools
import matplotlib.pyplot as plt
import networkx as nx
import time
import pandas as pd
import sys

from .utils import *
from .graph import *


class Variable:
    def __init__(self, func):
        self.func = func
        self.name = None
        self._settings = None
        self.result = None
        self.runtime = 0

    def __repr__(self):
        return f"V: {self.func.__name__}"

    def __call__(self, t):
        if t < 0 or t > self.settings["T_MAX_CALCULATION"]:
            return 0

        if self.settings.get("DEVELOP") is None:
            if self.result[t] is None:
                return self.func(t)

        return self.result[t]

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, new_settings):
        self._settings = new_settings
        self.result = [None for _ in range(0, self.settings["T_MAX_CALCULATION"]+1)]

    def calculate_t(self, t):
        self.result[t] = self.func(t)
        return self.result[t]


def variable():
    """Decorator"""
    def wrapper(func):
        func = functools.lru_cache(func)
        variable = Variable(func)
        return variable
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
    """Set of model points."""

    def __init__(self, data, name=None, settings=None):
        self.model_point_set_data = data
        self.name = name
        self.settings = settings
        self._id = None
        self.model_point_data = None
        self.model_point_size = None

    def __repr__(self):
        return f"ModelPointSet: {self.name}"

    def __len__(self):
        return self.model_point_set_data.shape[0]

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

        if new_id not in self.model_point_set_data.index:
            raise CashflowModelError(f"There is no id '{new_id}' in model_point_set '{self.name}'.")

        self.model_point_data = self.model_point_set_data.loc[[new_id]]
        self.model_point_size = self.model_point_data.shape[0]

    def initialize(self):
        """Name and settings are not present while creating object."""
        self.perform_checks()
        self.set_index()
        self.id = self.model_point_set_data.iloc[0][self.settings["ID_COLUMN"]]

    def perform_checks(self):
        # Check ID columns
        id_column = self.settings["ID_COLUMN"]
        if id_column not in self.model_point_set_data.columns:
            raise CashflowModelError(f"\nThere is no column '{id_column}' in model_point_set '{self.name}'.")

        # Check unique keys in main
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


class Model:
    """Actuarial cash flow model.
    Model combines model variables and model point sets.
    """
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
        print_log(f"Start run for model '{self.name}'", one_core)

        DG = self.create_graph()

        # Get an order of calculations
        ordered_nodes = []
        while DG.nodes:
            nodes_without_predecessors = [node for node in DG.nodes if len(list(DG.predecessors(node))) == 0]
            ordered_nodes.append(nodes_without_predecessors)
            DG.remove_nodes_from(nodes_without_predecessors)
        ordered_nodes = flatten(ordered_nodes)

        # Iterate over model points
        main = get_object_by_name(self.model_point_sets, "main")
        print_log(f"Total number of model points: {main.model_point_set_data.shape[0]}", one_core)
        if one_core and self.settings["MULTIPROCESSING"]:
            if len(main) > self.cpu_count:
                print_log(f"Multiprocessing on {self.cpu_count} cores")
                print_log(f"Calculation of ca. {len(main) // self.cpu_count} model points per core")

        # Set calculation ranges for multiprocessing
        range_start = None
        range_end = None
        if self.settings["MULTIPROCESSING"]:
            main_ranges = split_to_ranges(len(main), self.cpu_count)
            # Number of model points is lower than the number of cpus, only calculate on the 1st core
            if part >= len(main_ranges):
                return None
            range_start, range_end = main_ranges[part]

        # Create partial calculation function for map
        progressbar_max = len(main) if range_end is None else range_end
        p = functools.partial(self.calculate_model_point, ordered_nodes=ordered_nodes, one_core=one_core,
                              progressbar_max=progressbar_max)

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

        # Get runtime
        runtime = None
        if self.settings["SAVE_RUNTIME"]:
            runtime = pd.DataFrame({
                "variable": [v.name for v in self.variables],
                "runtime": [v.runtime for v in self.variables]
            })

        return result, runtime

    def create_graph(self):
        # Create directed graph for all variable-period tuples
        DG = nx.DiGraph()
        for variable in self.variables:
            for period in range(0, self.settings["T_MAX_CALCULATION"] + 1):
                DG.add_node((variable, period))

        # Create dependencies
        variable_names = [variable.name for variable in self.variables]
        dependencies = []
        for variable in self.variables:
            variable_dependencies = get_dependencies(variable.func, variable_names, self.settings)
            dependencies.append(variable_dependencies)
        dependencies = flatten(dependencies)

        for dependency in dependencies:
            dependency.func = get_object_by_name(self.variables, dependency.func)
            dependency.call = get_object_by_name(self.variables, dependency.call)

        # Add edges to the graph
        for dependency in dependencies:
            add_edges_from_dependency(dependency, DG, self.settings["T_MAX_CALCULATION"]+1)

        # Draw graph in admin mode
        if self.settings.get("ADMIN_DRAW") is not None:
            nx.draw(DG, with_labels=True)
            plt.show()

        return DG

    def calculate_model_point(self, row, ordered_nodes, one_core, progressbar_max):
        main = get_object_by_name(self.model_point_sets, "main")

        # Set model point's id
        model_point_id = main.model_point_set_data.index[row]
        for model_point_set in self.model_point_sets:
            model_point_set.id = model_point_id

        # Perform calculations
        for node in ordered_nodes:
            variable = node[0]
            t = node[1]
            if self.settings.get("ADMIN_NODE") is not None:
                print(f"Node: ({variable.name}, {t})")
            if t < 0 or t > self.settings["T_MAX_CALCULATION"]:
                continue
            start = time.time()
            variable.calculate_t(t)
            variable.runtime += time.time() - start

        # Get results and trim for T_MAX_OUTPUT
        columns = [variable.name for variable in self.variables]
        data = [variable.result[:self.settings["T_MAX_OUTPUT"]+1] for variable in self.variables]
        data = map(list, zip(*data))  # transpose
        data_frame = pd.DataFrame(data, columns=columns)

        # Results may contain subset of columns
        if len(self.settings["OUTPUT_COLUMNS"]) > 0:
            data_frame = data_frame[self.settings["OUTPUT_COLUMNS"]]

        # Clear cache
        if self.settings.get("DEVELOP") is None:
            for variable in self.variables:
                variable.func.cache_clear()

        # Update progessbar
        if one_core:
            updt(progressbar_max, row + 1)

        return data_frame
