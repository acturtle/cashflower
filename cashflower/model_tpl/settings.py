settings = {
    # Grouping variable for model points (None aggregates all; otherwise, groups by the specified variable)
    "GROUP_BY": None,

    # Enable multiprocessing (set to True to use multiple CPUs)
    "MULTIPROCESSING": False,

    # Number of stochastic scenarios to simulate (None for deterministic)
    "NUM_STOCHASTIC_SCENARIOS": None,

    # Variables to include in the model output (None includes all variables)
    "OUTPUT_VARIABLES": None,

    # Whether to save diagnostic data (True or False)
    "SAVE_DIAGNOSTIC": False,

    # Whether to save log data (True or False)
    "SAVE_LOG": False,

    # Whether to save the model's output data (True or False)
    "SAVE_OUTPUT": True,

    # Maximum time step for calculations (default is 720)
    "T_MAX_CALCULATION": 720,

    # Maximum time step for output (default is 720)
    "T_MAX_OUTPUT": 720,
}
