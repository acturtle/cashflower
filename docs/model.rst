Model
=====

The :code:`model.py` script contains the definitions of model variables, which serve as the core components
of the actuarial cash flow model, encapsulating its logic.

|

..  code-block:: python

    @variable()
    def my_variable(t):
        ...

To define a model variable, follow two steps:

#. Define a function with the :code:`t` parameter (or no parameters) that returns a numeric value.
#. Decorate the function with :code:`@variable()`.

|

Model variables produce results per model point and time.

.. image:: https://acturtle.com/static/img/31/all.png
   :align: center

Regarding time dependence, there are two types of variables:

* A - time-dependent variable,
* B - constant variable.

Both types are described further in the sections below.

|

In :code:`cashflower`, you can define array variables for enhanced runtime efficiency.
Array variables are covered in detail in the :doc:`advanced` section of this documentation.

|

Time-dependent variable
^^^^^^^^^^^^^^^^^^^^^^^

To define a time-dependent variable, create a function with the parameter :code:`t`
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
