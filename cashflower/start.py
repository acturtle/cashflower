import importlib
import inspect


from . import CashflowModelError, ModelVariable, ModelPoint, Model, Parameter, Runplan


def load_settings(settings=None):
    """Load model settings.

    The function firstly reads the default settings and then overwrites these that have been defined by the user.
    The function helps with backward compatibility.
    If there is a new setting in the package, the user doesn't have to have it in the settings script.

    Parameters
    ----------
    settings : dict
        Model settings defined by the user.

    Returns
    -------
    dict
        Full set of settings.
    """
    if settings is None:
        settings = dict()

    initial_settings = {
        "AGGREGATE": True,
        "OUTPUT_COLUMNS": [],
        "POLICY_ID_COLUMN": "policy_id",
        "SAVE_RUNTIME": False,
        "T_CALCULATION_MAX": 1200,
        "T_OUTPUT_MAX": 1200,
    }

    for key, value in settings.items():
        initial_settings[key] = value

    return initial_settings


def get_runplan(input_members):
    runplan = None
    for name, item in input_members:
        if isinstance(item, Runplan):
            runplan = item
            break
    return runplan


def get_modelpoints(input_members, settings):
    policy_id_column = settings["POLICY_ID_COLUMN"]
    modelpoint_members = [m for m in input_members if isinstance(m[1], ModelPoint)]

    policy = None
    modelpoints = []
    for name, modelpoint in modelpoint_members:
        modelpoint.name = name
        modelpoint.settings = settings
        modelpoints.append(modelpoint)

        # Policy_id is a key for model points
        if policy_id_column not in modelpoint.data.columns:
            raise CashflowModelError(f"\nThere is no column '{policy_id_column}' in modelpoint '{name}'.")

        # Primary modelpoint must have unique keys
        if name == "policy":
            policy = modelpoint
            if not policy.data[policy_id_column].is_unique:
                raise CashflowModelError(
                    f"\nThe 'policy' modelpoint must have unique values in '{policy_id_column}' column.")

        # String ensures compatiblity of values
        modelpoint.data[policy_id_column] = modelpoint.data[policy_id_column].astype(str)

        # Policy_id is an index and a column
        modelpoint.data[policy_id_column + "_duplicate"] = modelpoint.data[policy_id_column]
        modelpoint.data = modelpoint.data.set_index(policy_id_column)
        modelpoint.data[policy_id_column] = modelpoint.data[policy_id_column + "_duplicate"]
        modelpoint.data = modelpoint.data.drop(columns=[policy_id_column + "_duplicate"])

    if policy is None:
        raise CashflowModelError("\nA model must have a modelpoint named 'policy'.")

    return modelpoints, policy


def get_variables(model_members, policy, settings):
    variable_members = [m for m in model_members if isinstance(m[1], ModelVariable)]
    variables = []
    for name, variable in variable_members:
        if variable.assigned_formula is None:
            raise CashflowModelError(f"\nThe '{name}' variable has no formula. Please check the 'model.py' script.")

        # Policy is a default modelpoint
        if variable.modelpoint is None:
            variable.modelpoint = policy

        variable.name = name
        variable.settings = settings
        variable.formula = variable.assigned_formula
        variables.append(variable)

    # Model variables can not be overwritten by formulas with the same name
    overwritten = list(set(ModelVariable.instances) - set(variables))
    if len(overwritten) > 0:
        for item in overwritten:
            if item.assigned_formula is None:
                msg = "\nThere are two variables with the same name. Please check the 'model.py' script."
                raise CashflowModelError(msg)
        names = [item.assigned_formula.__name__ for item in overwritten]
        names_str = ", ".join(names)
        msg = f"\nThe variables with the following formulas are not correctly handled in the model: \n{names_str}"
        raise CashflowModelError(msg)

    return variables


def get_parameters(model_members, policy):
    parameter_members = [m for m in model_members if isinstance(m[1], Parameter)]
    parameters = []
    for name, parameter in parameter_members:
        if parameter.assigned_formula is None:
            raise CashflowModelError(f"\nThe '{name}' parameter has no formula. Please check the 'model.py' script.")

        # Policy is a default modelpoint
        if parameter.modelpoint is None:
            parameter.modelpoint = policy

        parameter.name = name
        parameter.formula = parameter.assigned_formula
        parameters.append(parameter)

    return parameters


def start(model_name, settings, argv):
    settings = load_settings(settings)
    input_module = importlib.import_module(model_name + ".input")
    model_module = importlib.import_module(model_name + ".model")

    # input.py contains runplan and modelpoints
    input_members = inspect.getmembers(input_module)
    runplan = get_runplan(input_members)
    modelpoints, policy = get_modelpoints(input_members, settings)

    # model.py contains model variables and parameters
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, policy, settings)
    parameters = get_parameters(model_members, policy)

    # User can provide runplan version in CLI command
    if runplan is not None and len(argv) > 1:
        runplan.version = argv[1]

    model = Model(model_name, variables, parameters, modelpoints, settings)
    model.run()
