import importlib
import inspect


from . import CashflowModelError, ModelVariable, ModelPoint, Model, Constant, Runplan


def load_settings(settings=None):
    """Load model settings.
    
    The function firstly reads the default settings and then overwrites these that have been defined by the user.
    The function helps with backward compatibility.
    If there is a new setting in the package, the user doesn't have to have it in the settings script.

    Parameters
    ----------
    settings : dict
        Model settings defined by the user. (Default value = None)

    Returns
    -------
    dict
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
    """Get runplan object from input.py script.

    Parameters
    ----------
    input_members : list of tuples
        Items defined in input.py.

    Returns
    -------
    object of class Runplan
    """
    runplan = None
    for name, item in input_members:
        if isinstance(item, Runplan):
            runplan = item
            break
    return runplan


def get_modelpoints(input_members, settings):
    """Get model points from input.py script.

    Parameters
    ----------
    input_members : list of tuples
        Items defined in input.py.

    settings : dict
        Settings defined by the user.

    Returns
    -------
    Tuple, first item is a list of ModelPoint objects and second item is primary ModelPoint
    """
    modelpoint_members = [m for m in input_members if isinstance(m[1], ModelPoint)]

    policy = None
    modelpoints = []
    for name, modelpoint in modelpoint_members:
        modelpoint.name = name
        modelpoint.settings = settings
        modelpoint.initialize()
        modelpoints.append(modelpoint)
        if name == "policy":
            policy = modelpoint

    if policy is None:
        raise CashflowModelError("\nA model must have a modelpoint named 'policy'.")

    return modelpoints, policy


def get_variables(model_members, policy, settings):
    """Get model variables from input.py script.

    Parameters
    ----------
    model_members : list of tuples
        Items defined in input.py.

    policy : object of class ModelPoint
        Primary model point in the model.

    settings : dict
        Settings defined by the user.

    Returns
    -------
    List of ModelVariable objects.
    """
    variable_members = [m for m in model_members if isinstance(m[1], ModelVariable)]
    variables = []
    for name, variable in variable_members:
        variable.name = name
        variable.settings = settings
        variable.initialize(policy)
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


def get_constants(model_members, policy):
    """Get constants from input.py script.

    Parameters
    ----------
    model_members : list of tuples
        Items defined in input.py.
        
    policy : object of class ModelPoint
        Primary model point in the model.

    Returns
    -------
    List of Constant objects.
    """
    constant_members = [m for m in model_members if isinstance(m[1], Constant)]
    constants = []
    for name, constant in constant_members:
        constant.name = name
        constant.initialize(policy)
        constants.append(constant)
    return constants


def start(model_name, settings, argv):
    """Initiate a Model object and run it.

    Parameters
    ----------
    model_name : str
        Name of the model.
        
    settings : dict
        Settings defined by the user.

    argv : list
        List of terminal arguments.
    """
    settings = load_settings(settings)
    input_module = importlib.import_module(model_name + ".input")
    model_module = importlib.import_module(model_name + ".model")

    # input.py contains runplan and modelpoints
    input_members = inspect.getmembers(input_module)
    runplan = get_runplan(input_members)
    modelpoints, policy = get_modelpoints(input_members, settings)

    # model.py contains model variables and constants
    model_members = inspect.getmembers(model_module)
    variables = get_variables(model_members, policy, settings)
    constants = get_constants(model_members, policy)

    # User can provide runplan version in CLI command
    if runplan is not None and len(argv) > 1:
        runplan.version = argv[1]

    model = Model(model_name, variables, constants, modelpoints, settings)
    model.run()
