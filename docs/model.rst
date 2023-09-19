Model
=====

The :code:`model.py` script contains the definitions of model variables, which serve as the core components
of the actuarial cash flow model, encapsulating its logic.

To define a model variable, follow these steps:

1. Define a function with the :code:`t` parameter (or without any parameters) that return numeric values,
2. Decorate the function with :code:`@variable()`.

Model variables produce results per model point and time, with some remaining constant throughout.

.. image:: https://acturtle.com/static/img/31/all.png
   :align: center

There are two types of variables:

* A - time-dependent variable,
* B - constant variable.

Both types are described below.

.. WARNING::
    Model variables must return numeric values.

|

Time-dependent variable
^^^^^^^^^^^^^^^^^^^^^^^


o define a time-dependent variable, create a function with the parameter :code:`t`
and add the :code:`@variable()` decorator.

..  code-block:: python
    :caption: model.py

    @variable()
    def cal_month(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1

The variable can be called inside of another variable.

For example:

..  code-block:: python
    :caption: model.py

    @variable()
    def cal_year(t):
        ...
        cal_month(t-1)
        ...

|

Constant variable
^^^^^^^^^^^^^^^^^

To define time-independent variables, create a function without any parameters and add the :code:`@variable()` decorator.

..  code-block:: python
    :caption: model.py

    @variable()
    def elapsed_months():
        issue_year = main.get("issue_year")
        issue_month = main.get("issue_month")
        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


Constant variables, like :code:`elapsed_months`, maintain a consistent value throughout the projection,
making them independent of time. These variables do not require any arguments when called.

For example:

..  code-block:: python
    :caption: model.py

    @variable()
    def pol_month(t):
        ...
        mnth = elapsed_months() % 12
        ...

Constant variables are particularly useful for storing information that remains unchanged over time.

|

For more advanced types of variables, such as array variables, please refer to the :doc:`advanced` documentation.
