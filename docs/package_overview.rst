Package overview
================

The repository of the :code:`cashflower` package follows this structure:

.. code-block::

    .
    ├── .github/
    │   └── workflows/
    │       ├── build_deploy.yml
    │       └── pytest.yml
    ├── cashflower/
    │   ├── cython/              # Cython extension for performance optimization
    │   ├── model_tpl/           # Template for the cash flow model's structure
    │   ├── __init__.py          # Imports core components and utilities
    │   ├── core.py              # Main logic for cash flow models
    │   ├── error.py             # Custom error definitions
    │   ├── graph.py             # Dependency graph creation
    │   ├── reader.py            # CSV file reader class
    │   ├── start.py             # Entry point and model initialization
    │   └── utils.py             # Utility functions
    ├── dev_models/              # Fully-functioning models for development checks
    ├── docs/                    # Documentation files
    ├── tests/                   # Unit tests
    ├── .gitignore               # Ignored files for version control
    ├── .readthedocs.yaml        # Configuration for ReadTheDocs platform
    ├── LICENSE                  # License information
    ├── MANIFEST.in              # Specifies non-python files for packaging
    ├── pyproject.toml           # Configuration settings for build system and tools
    ├── README.md                # Main repository README
    ├── requirements.txt         # Required Python packages for developers
    └── setup.py                 # Main setup file for package building


In this section, we'll briefly describe the purpose of each file and folder.

|

Source files
------------

The :code:`cashflower` folder contains the core package source code. Here are the key files:

- :code:`core.py` - contains the main logic for cash flow models,
- :code:`error.py` - defines custom error class,
- :code:`graph.py` - handles dependency graph creation for model variables and calculation order,
- :code:`reader.py` - provides a class for reading CSV files,
- :code:`start.py` - serves as the entry point for the package, initializing components and creating Model instances,
- :code:`utils.py` - contains utility functions.

|

Supporting files
----------------

Supporting files are categorized into testing, documentation, and configuration:

**Testing:**

- :code:`dev_models` - fully-functioning models for development checks,
- :code:`tests` - contains unit tests.


**Documentation:**

- :code:`docs` - stores documentation files,
- :code:`README.md` - the main README file displayed on the repository's main page.

**Configuration:**

- :code:`.github/workflows` - contains GitHub workflows that are automatically triggered,
- :code:`.gitignore` - lists files to be ignored by version control,
- :code:`.readthedocs.yaml` - configuration for the ReadTheDocs platform,
- :code:`MANIFEST.in` - specifies non-Python files to include in the package that might be ignored by packaging tools,
- :code:`pyproject.toml` - configuration settings for build systems and tools,
- :code:`requirements.txt` - lists Python packages required for developers of the package,
- :code:`setup.py` - the primary setup file for building the package.

|
