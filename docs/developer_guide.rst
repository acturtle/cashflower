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
    * :code:`Variable`,
    * :code:`Model`.

The model object that has been created in the :code:`start.py` script creates a queue of model variables
in a way that there are no calculation conflicts.
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
