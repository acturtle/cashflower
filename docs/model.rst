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

