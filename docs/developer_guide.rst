Developer guide
===============

Overview
--------

The code in the cashflower package helps to transform the formulas defined by the user into the output reports.

|

**start.py**

As a first step, the user needs to create a model. The :code:`create_model()` function copies template files
from the :code:`model_tpl` folder and replaces parts that require a model name.

Once the user has populated files with the formulas, the model gets started using code in the :code:`start.py` script.

The :code:`start()` function gathers all components of the model:
    * settings from :code:`settings.py`,
    * model point sets and runplan from :code:`input.py`,
    * model variables and constants from :code:`model.py`.

After that, it creates the instance of the :code:`Model` class which is used to calculate and save the results.

|

**cashflow.py**

The :code:`cashflow.py` script contains the classes for all the main objects, such as:
    * :code:`Runplan`,
    * :code:`ModelPointSet`,
    * :code:`ModelVariable`,
    * :code:`Constant`,
    * :code:`Model`.

The model object that has been created in the :code:`start.py` script creates a queue of model components (variables and constants) in a way that there are no calculation conflicts.
After that, it iterates over each policy and calculates results for all of the components.

Once the calculation is complete, the results are saved to the flat files with comma separated values.

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

Data flow
----------

This section describes the data flow of the results within the model.

|

**Structure of results**

The structure of the results is kept in the :code:`col_dict` variable.

..  code-block:: python

    col_dict = {
        "main": {
            "ModelVariable" = ["pv_premium", "bel"],
            "Constant"      = ["sa_code"],
        },
        "fund": {
            "ModelVariable" = ["fund_value"],
            "Constant"      = [],
        },
    }

The :code:`col_dict` is a dictionary of dictionaries.
The keys of the outer dictionary are the names of the model point sets.
The keys of the inner dictionaries are two types of model components, i.e.: :code:`ModelVariable` and :code:`Constant`.
The values are the names of the columns to be outputted.

|

**Model point output**

Based on the structure of the results, the model point output gets created.
The structure of the :code:`model_point_output` is similar to :code:`col_dict`.
However, the values are numpy matrices (2D arrays) instead of lists of names.

..  code-block:: python

    import numpy as np

    model_point_output = {
        "main": {
            "ModelVariable" = np.array(shape=(n1, m1)),
            "Constant"      = np.array(shape=(n2, m2)),
        },
        "fund": {
            "ModelVariable" = np.array(shape=(n3, m3)),
            "Constant"      = np.array(shape=(n4, m4)),
        },
    }


The values of the inner dictionary are numpy matrices with :code:`n` rows and :code:`m` columns, where:
    * :code:`n` - the number of projection months (multiplied by the number of records if the output is individual),
    * :code:`m` - the number of columns.

The :code:`model_point_output` gets populated with the results separately for each model point.

|

**Model output**

The single model point outputs are stored in a list and then merged into the full model output.
Model output has an analogous structure to model point output.

..  code-block:: python

    model_output = {
        "main": {
            "ModelVariable" = np.array(shape=(n1, m1)),
            "Constant"      = np.array(shape=(n2, m2)),
        },
        "fund": {
            "ModelVariable" = np.array(shape=(n3, m3)),
            "Constant"      = np.array(shape=(n4, m4)),
        },
    }


The way the results are merged depends on the setting. If:
    * :code:`AGGREGATE=True`  - the model point outputs are summed,
    * :code:`AGGREGATE=False` - the model point outputs are concatenated.

The number of rows equals the number of projection periods (multiplied by the number of records for all model points
if the output is individual). The number of columns amounts to the number of model components.

The model output is returned in the :code:`run.py` script.
