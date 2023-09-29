Developer guide
===============

Overview
--------

The repository of the :code:`cashflower` package follows this structure:

.. code-block::

    .
    ├── .github/
    │   └── workflows/
    │       ├── deploy.yml
    │       └── pytest.yml
    ├── cashflower/
    │   ├── model_tpl/           # Template for the cash flow model's structure (for users)
    │   ├── __init__.py
    │   ├── cashflow.py          # Main logic for cash flow models
    │   ├── error.py             # Custom error definitions
    │   ├── graph.py             # Dependency graph creation
    │   ├── reader.py            # CSV file reader class
    │   ├── start.py             # Entry point and model initialization
    │   └── utils.py             # Utility functions
    ├── dev_models/              # Fully-functioning models for development checks
    ├── docs/                    # Documentation files
    ├── tests/                   # Unit tests
    ├── tutorials/               # Tutorials and guides
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

Package source
^^^^^^^^^^^^^^

The :code:`cashflower` folder contains the core package source code. Here are the key files:

- :code:`cashflow.py` - contains the main logic for cash flow models,
- :code:`error.py` - defines custom error class,
- :code:`graph.py` - handles dependency graph creation for model variables and calculation order,
- :code:`reader.py` - provides a class for reading CSV files,
- :code:`start.py` - serves as the entry point for the package, initializing components and creating Model instances,
- :code:`utils.py` - contains utility functions.

|

Supporting files
^^^^^^^^^^^^^^^^

Supporting files are categorized into testing, documentation, and configuration:

**Testing:**

- :code:`tests` - contains unit tests,
- :code:`dev_models` - fully-functioning models for development checks.

**Documentation:**

- :code:`docs` - stores documentation files,
- :code:`README.md` - the main README file displayed on the repository's main page.

**Configuration:**

- :code:`setup.py` - the primary setup file for building the package,
- :code:`pyproject.toml` - configuration settings for build systems and tools,
- :code:`.github/workflows` - contains GitHub workflows that are automatically triggered,
- :code:`.gitignore` - lists files to be ignored by version control,
- :code:`.readthedocs.yaml` - configuration for the ReadTheDocs platform.
- :code:`requirements.txt` - lists Python packages required for developers of the package.
- :code:`MANIFEST.in` - specifies non-Python files to include in the package that might be ignored by packaging tools.

|

Branching policy
----------------

The picture shows the branches used in the cashflower package.

.. image:: https://acturtle.com/static/img/docs/branches.png

Branches:
    * main - the official version:
        * the same code as on PyPI
        * accepts pull requests from the *develop* branch
        * used for Read The Docs (RTD)
        * released to PyPI by setting a tag

    * develop - the development version:
        * new PyPI release candidate
        * accepts pull requests from *feature/<name>* branches
        * central point for all new features
        * only minor fixes are done here
        * greater version number than the *main* branch

    * feature/<name> - new functionalities:
        * place to work on new features
        * pushed to the *develop* branch (via pull request)
        * the same version number as the *develop* branch

|

Development testing
-------------------

During the development of the "cashflower" package, three types of tests should be used:

1. **Unit tests**

   Unit tests evaluate individual functionalities of the package. These tests are stored in the :code:`tests` folder.
   To execute unit tests, use the following command:

   .. code-block::

      pytest

2. **Development models**

   The cashflower package serves as a framework for actuarial cash flow models.
   It's essential that the development process does not affect the various settings that models may employ.

   The :code:`dev_models` folder contains a variety of models, each with different model points, settings, and variables.
   Detailed descriptions of these models can be found in the :code:`instructions.md` file.

   To perform checks on the models, follow these steps:

   a. Before making any changes, run :code:`01_initial_runs.py`.
   b. After completing the development, run :code:`02_perform_checks.py` to ensure that the code changes have no adverse impact on any of the models.

3. **Static tests (linting)**

   Static tests, also known as linting, validate the code's syntax and alignment with PEPs (Python Enhancement Proposals).

   To run static tests, use the following command:

   .. code-block::

      ruff cashflower

   You will be notified of any code violations.

|

Calculation order
-----------------

In a cash flow model, variables often depend on other variables, creating a complex web of dependencies.
To prevent recursion errors and ensure accurate calculations, the model follows a specific order when processing these
variables.

1. **Directed Graph**: The model identifies dependencies by creating a directed graph, revealing which variables call other variables.

2. **Initialization**: Variables without any predecessors are calculated first. They are removed from the graph, and the process continues until all such variables are processed.

3. **Handling Cycles**: If there are variables with cyclic dependencies, they are assigned the same calculation order index and computed simultaneously.

This approach guarantees that variables are calculated in an order that respects their dependencies and mitigates the risk of recursion errors.

|

Ordering example
^^^^^^^^^^^^^^^^

**Step 1:** The model consists of 8 variables. Two of these variables, :code:`A` and :code:`B`, do not have any predecessors.
To determine the calculation order, we start with the first variable in alphabetical order, which is :code:`A`.
We assign it a calculation order of :code:`1` and remove it from the calculation graph.

.. image:: https://acturtle.com/static/img/docs/calc_order_01.png
   :align: center

**Step 2:** Now, the only remaining variable without predecessors is :code:`B`.
We assign it a calculation order of :code:`2` and remove it from the graph.

.. image:: https://acturtle.com/static/img/docs/calc_order_02.png
   :align: center

**Step 3**: At this point, there are no more variables without predecessors because there is a cyclic dependency between variables :code:`C`, :code:`D`, and :code:`E`.
To handle cyclic dependencies, we assign the entire cycle the same calculation order, which is :code:`3`, indicating that these variables will be evaluated simultaneously.
Afterward, all three variables are removed from the graph.

.. image:: https://acturtle.com/static/img/docs/calc_order_03.png
   :align: center

**Step 4**: The process continues until all variables have been assigned a calculation order.
The next variables to be processed are :code:`F` with an order of :code:`4`, :code:`G` with an order of :code:`5`, and :code:`H` with an order of :code:`6`.

.. image:: https://acturtle.com/static/img/docs/calc_order_04.png
   :align: center

|

Output subset
^^^^^^^^^^^^^

Users have the flexibility to choose a specific subset of output columns through the :code:`OUTPUT_COLUMNS` setting.

For instance, let's consider a scenario where the user has configured their settings to output only the variable :code:`F`:

..  code-block:: python
    :caption: settings.py

    settings = {
        "OUTPUT_COLUMNS": ["F"],
    }

In this case, variables :code:`G` and :code:`H` are not required for the desired output and can be safely omitted from the calculation graph and the model itself.

.. image:: https://acturtle.com/static/img/docs/calc_order_05.png
   :align: center

The model only needs to evaluate variable :code:`F` and its predecessors.

|

Memory management
-----------------

Memory management is an important aspect of cash flow modelling. Efficiently managing memory is essential when dealing
with different model configurations and output sizes. Several factors impact the amount of memory consumed during
the modeling process.

Memory consumption
^^^^^^^^^^^^^^^^^^

Factors affecting memory consumption:

1. **Aggregation**:
The :code:`AGGREGATE` setting determines whether the model returns the sum of all results (aggregated) or concatenated individual results.

2. **Projection period**:
The :code:`T_MAX_OUTPUT` setting specifies how many projection periods should be included in the output. A larger projection period increases memory usage.

3. **Number of variables:**
The :code:`OUTPUT_COLUMNS` setting specifies which variables should be part of the output.

The estimated output memory usage:

* :code:`t * v * 8` bytes - for the aggregated output,
* :code:`t * mp * v * 8` bytes - for the individual output.

where:

* :code:`t` - the number of future periods,
* :code:`v` - the number of variables,
* :code:`mp` - the number of model points.

The number of cells are multiplied by :code:`8` because results store 64-bit floats.


Approach
^^^^^^^^

Approach to memory management depends on whether the results are to be aggregated or individual.

**Aggregated output**

For aggregated output, the final result has :code:`t` rows and :code:`v` columns.
However, during calculations, results for each model point are generated individually.
To optimize memory, results are calculated in batches and aggregated after each batch, freeing up memory.
The batch size is determined based on available RAM.

**Individual output**

In the case of individual output, where the final result has :code:`t * mp` rows and :code:`v` columns,
the entire output object must fit into RAM. The model checks if the output size is within the total available RAM.
If it is, an empty results object is created to allocate memory, which is then filled with calculation results.

For individual results that exceed RAM capacity, an alternative approach is to calculate batches of model points
iteratively and save the results to a CSV file. In this scenario, the :code:`output` DataFrame will not be returned
in the :code:`run.py` script. If you require this feature, please contact us, and we can help with its implementation.

|
