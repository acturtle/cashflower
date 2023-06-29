Model
=====

The logic of the model is defined in the :code:`model.py` script.
The components of the model are time-dependent variables.


|

To define model variable, write a function with argument :code:`t` and add :code:`variable()` decorator:

..  code-block:: python
    :caption: model.py

    from cashflower import variable

    PREMIUM = 250

    @variable()
    def pv_premium(t):
        return pv_premium(t+1) * (1/1.05) + PREMIUM

|
