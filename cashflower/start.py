import importlib
import inspect


from . import CashflowModelError, ModelVariable, ModelPoint, Model


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
        "POLICY_ID_COLUMN": "POLICY_ID",
        "SAVE_RUNTIME": False,
        "T_CALCULATION_MAX": 1440,
        "T_OUTPUT_MAX": 1440,
    }

    for key, value in settings.items():
        initial_settings[key] = value

    return initial_settings


def get_model_input(modelpoint_module, model_module, settings):
    """Prepare input for model.

    Gathers all model points and model variable instances.
    Assigns names to model variables and, if not assigned by user, also model points.
    (User doesn't have to assign a model point to a model variable if there is only one model point.)

    Performs checks:
    - model has a modelpoint named 'policy'

    Parameters
    ----------
    modelpoint_module : module
        Module where user defines model points.
    model_module : module
        Module where user defines model variables.
    settings : dict
        Dictionary with user settings.

    Returns
    -------
    tuple
        Contains two lists - model variables and model points.
    """
    policy_id_column = settings["POLICY_ID_COLUMN"]

    # Gather model points
    modelpoint_members = inspect.getmembers(modelpoint_module)
    modelpoint_members = [m for m in modelpoint_members if isinstance(m[1], ModelPoint)]

    policy = None
    modelpoints = []
    for name, modelpoint in modelpoint_members:
        modelpoint.name = name
        modelpoint.settings = settings
        modelpoints.append(modelpoint)

        if name == "policy":
            policy = modelpoint

        if policy_id_column not in modelpoint.data.columns:
            raise CashflowModelError(f"There is no column '{policy_id_column}' in modelpoint '{name}'.")

    if policy is None:
        raise CashflowModelError("A model must have a modelpoint named 'policy'.")

    # Gather model variables
    model_members = inspect.getmembers(model_module)
    model_members = [m for m in model_members if isinstance(m[1], ModelVariable)]

    variables = []
    for name, variable in model_members:
        variable.name = name
        if variable.assigned_formula is None:
            raise CashflowModelError("A model variable exists without an assigned formula. Please check the model.")
        variable.formula = variable.assigned_formula
        variable.settings = settings
        if variable.modelpoint is None:
            variable.modelpoint = policy
        variables.append(variable)

    # Ensure that model variables are not overwritten by formulas with the same name
    overwritten = list(set(ModelVariable.instances) - set(variables))
    if len(overwritten) > 0:
        names = [item.assigned_formula.__name__ for item in overwritten]
        names_str = ", ".join(names)
        raise CashflowModelError(f"Ensure that model variable and formula have different names. "
                                 f"Please check: {names_str}")

    return variables, modelpoints


def start(model_name, settings):
    settings = load_settings(settings)
    modelpoint_module = importlib.import_module(model_name + ".modelpoint")
    model_module = importlib.import_module(model_name + ".model")
    variables, modelpoints = get_model_input(modelpoint_module, model_module, settings)
    model = Model(variables, modelpoints, settings)
    model.run()
