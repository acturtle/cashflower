Testing
=======

During the development of the "cashflower" package, three types of tests should be used:

1. **Unit tests**

   Unit tests evaluate individual functionalities of the package. These tests are stored in the :code:`tests` folder.
   To execute unit tests, use the following command:

   .. code-block::

      pytest

|

2. **Development models**

   The cashflower package serves as a framework for actuarial cash flow models.
   It's essential that the development process does not affect the various settings that models may employ.

   The :code:`dev_models` folder contains a variety of models, each with different model points, settings, and variables.
   Detailed descriptions of these models can be found in the :code:`instructions.md` file.

   To perform checks on the models, follow these steps:

   a. Before making any changes, run :code:`01_initial_runs.py`.
   b. After completing the development, run :code:`02_perform_checks.py` to ensure that the code changes have no adverse impact on any of the models.

|

3. **Static tests (linting)**

   Static tests, also known as linting, validate the code's syntax and alignment with PEPs (Python Enhancement Proposals).

   To run static tests, use the following command:

   .. code-block::

      ruff cashflower

   You will be notified of any code violations.

|
