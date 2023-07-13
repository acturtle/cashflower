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

To define a constant (time-independet) model variable, write a function without any parameters and decorate it with :code:`variable`.
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

