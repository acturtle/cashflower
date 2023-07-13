Model
=====

The logic of the model is defined in the :code:`model.py` script.
The components of the model are time-dependent variables.


|

To define a time-dependent model variable, write a function with parameter :code:`t` and add :code:`@variable()` decorator:

..  code-block:: python
    :caption: model.py

    from cashflower import variable

    @variable()
    def projection_year(t):
        if t == 0:
            return 0
        elif t % 12 == 1:
            return projection_year(t - 1) + 1
        else:
            return projection_year(t - 1)
|

To define a constant (time-independent) model variable, write a function without any parameters and decorate it with :code:`variable`.
The result for such a variable will be the same for all future projection periods.

..  code-block:: python
    :caption: model.py

    @variable()
    def elapsed_months():
        issue_year = main.get("issue_year")
        issue_month = main.get("issue_month")
        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


If the variable has the same results for all model points, you can add :code:`repeat=True` argument in the :code:`@variable` decorator.

..  code-block:: python
    :caption: model.py

    @variable(repeat=True)
    def cal_year(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)

The variable will be calculated only for the first model point and it the results will be repeated for all other model points.
This argument helps to decrease runtime of the model.
