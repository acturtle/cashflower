import functools
import matplotlib.pyplot as plt
import networkx as nx
import time
import pandas as pd
import sys

from .utils import *
from .graph import *


def raise_error_if_incorrect_argument(node):
    if len(node.args) != 1:
        msg = f"Model variable must have one argument. Please review the call of '{node.func.id}'."
        raise ValueError(msg)

    # Model variable can only call t, t+/-x, and x
    arg = node.args[0]
    msg = f"\nPlease review '{node.func.id}'. The argument of a model variable can be only:\n" \
          f"- t,\n" \
          f"- t plus/minus integer (e.g. t+1 or t-12),\n" \
          f"- an integer (e.g. 0 or 12)."

    # The model variable calls a variable
    if isinstance(arg, ast.Name):
        if not arg.id == "t":
            raise ValueError(msg)

    # The model variable calls a constant
    if isinstance(arg, ast.Constant):
        if not isinstance(arg.value, int):
            raise ValueError(msg)

    # The model variable calls an operation
    if isinstance(arg, ast.BinOp):
        check1 = isinstance(arg.left, ast.Name) and arg.left.id == "t"
        check2 = isinstance(arg.op, ast.Add) or isinstance(arg.op, ast.Sub)
        check3 = isinstance(arg.right, ast.Constant) and isinstance(arg.right.value, int)
        if not (check1 and check2 and check3):
            raise ValueError(msg)

    # The model variable calls something else
    if not (isinstance(arg, ast.Name) or isinstance(arg, ast.Constant) or isinstance(arg, ast.BinOp)):
        raise ValueError(msg)


def get_calls(func, variables):
    variable_names = [variable.name for variable in variables]
    visitor = Visitor(variable_names)
    node = ast.parse(inspect.getsource(func))
    # print("\n", ast.dump(node, indent=2))
    visitor.visit(node)
    call_names = visitor.calls
    calls = [get_object_by_name(variables, call_name) for call_name in call_names]
    return calls


def get_predecessors(node, DG):
    queue = Queue()
    visited = []

    queue.put(node)
    visited.append(node)

    while not queue.empty():
        node = queue.get()
        for child in DG.predecessors(node):
            if child not in visited:
                queue.put(child)
                visited.append(child)

    return visited


class Visitor(ast.NodeVisitor):
    def __init__(self, variable_names):
        self.variable_names = variable_names
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.variable_names:
                raise_error_if_incorrect_argument(node)
                self.calls.append(node.func.id)


class Variable:
    def __init__(self, func):
        self.func = func
        self.name = None
        self._settings = None
        self.result = None

        self.calls = None
        self.calc_order = None
        self.cycle = False
        self.direction = "asc"

        self.runtime = 0

    def __repr__(self):
        return f"V: {self.func.__name__}"

    def __call__(self, t):
        if t < 0 or t > self.settings["T_MAX_CALCULATION"]:
            raise CashflowModelError(f"Variable {self.name} has been called for period {t}.")

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


def variable():
    """Decorator"""
    def wrapper(func):
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


class ModelPointSet:
    """Set of model points."""

    def __init__(self, data, name=None, settings=None):
        self.data = data
        self.name = name
        self.settings = settings
        self._id = None
        self.model_point_data = None

    def __repr__(self):
        return f"ModelPointSet: {self.name}"

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
        """Name and settings are not present while creating object."""
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
        print_log(f"Building model '{self.name}'", one_core)

        # Create directed graph
        DG = self.create_graph()

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
                for cycle_without_predecessors in cycles_without_predecessors:
                    calc_order += 1
                    for node in cycle_without_predecessors:
                        node.calc_order = calc_order
                        node.cycle = True
                    DG.remove_nodes_from(cycle_without_predecessors)

        # Sort variables for calculation order
        self.variables = sorted(self.variables, key=lambda x: (x.calc_order, x.name))

        # Iterate over model points
        main = get_object_by_name(self.model_point_sets, "main")
        print_log(f"Total number of model points: {main.data.shape[0]}", one_core)
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
        # Get variables' calls
        for variable in self.variables:
            variable.calls = get_calls(variable.func, self.variables)

        # Create directed graph for all variables
        DG = nx.DiGraph()
        for variable in self.variables:
            DG.add_node(variable)
            for predecessor in variable.calls:
                DG.add_edge(predecessor, variable)
        return DG

    def calculate_model_point(self, row, ordered_nodes, one_core, progressbar_max):
        main = get_object_by_name(self.model_point_sets, "main")

        # Set model point's id
        model_point_id = main.data.index[row]
        for model_point_set in self.model_point_sets:
            model_point_set.id = model_point_id

        # Perform calculations
        for variable in self.variables:
            start = time.time()
            variable.calculate()
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
