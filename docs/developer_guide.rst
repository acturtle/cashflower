Developer guide
===============

Overview
--------

The code in the cashflower package helps to transform the formulas defined by the user into the output reports.

|

**admin.py**

As a first step, the user needs to create a model. The code in the :code:`admin.py` script helps with this step.
The :code:`create_model()` function copies template files from the :code:`model_tpl` folder and replaces parts that require a model name.

|

**start.py**

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

Various
-------

The :code:`t` and :code:`r` variables are system variables.

The :code:`t` variable represents time.
The :code:`r` variable represents the record number of the model point.

These two variables are added at different stages of the process depending on the settings.

The table below indicates where the variables are added to the output:

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - AGGREGATE
     - MULTIPROCESSING
     - Function
   * - True
     - False
     - :code:`calculate()`
   * - True
     - True
     - :code:`merge_and_save_multiprocessing()`
   * - False
     - False
     - :code:`calculate_single_model_point()`
   * - False
     - True
     - :code:`calculate_single_model_point()`
