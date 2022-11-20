Model
=====

The logic of the model is defined in the :code:`model.py` script.

The components of the model are :code:`ModelVariable` and :code:`Parameter`.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable, Parameter

    premium = Parameter()
    pv_premium = ModelVariable()


    @assign(premium)
    def premium_formula():
        return 100


    @assign(pv_premium)
    def pv_premium_formula(t):
        return pv_premium(t+1) * (1/1.05) + premium()


Model variable
--------------

Model variable is the main building block of the actuarial cash flow model.

|

**Create model variable**

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    pv_premium = ModelVariable()

    @assign(pv_premium)
    def pv_premium_formula(t):
        return pv_premium(t+1) * (1/1.05) + 100

There are two steps to define a model variable:
    #. Create an instance of the :code:`ModelVariable` class.
    #. Assign a :code:`t`-dependent formula to the variable.

The first step is to create a variable, which is an instance of the :code:`ModelVariable` class.

..  code-block:: python
    :caption: model.py

    pv_premium = ModelVariable()

Once the variable is created, use the decorator :code:`assign()` to link a formula to the variable.

:code:`assign()` take as an argument a model variable.

..  code-block:: python
    :caption: model.py

    @assign(pv_premium)

:code:`assign()` decorates the function with the parameter :code:`t`.

.. IMPORTANT::
    The function of the model variable must have only one parameter :code:`t`.

The function contains the logic for the calculation.

..  code-block:: python
    :caption: model.py

    def pv_premium_formula(t):
        return pv_premium(t+1) * (1/1.05) + 100

|

**Use other variable in calculation**

Variables can be used in each other formulas.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    a = ModelVariable()
    b = ModelVariable()

    @assign(a)
    def a_formula(t):
        return 10 * t

    @assign(b)
    def b_formula(t):
        return a(t) + 3

To use another variable, call a **variable** for the given :code:`t`.

.. IMPORTANT::
    To use results of :code:`a` variable, call :code:`a(t)` and **not** :code:`a_formula(t)`.

A variable can also call itself for a different time. This functionality can be useful for discounting.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    c = ModelVariable()

    @assign(c)
    def c_formula(t):
        if t == 1200:
            return 100
        return c(t+1) * (1/1.05)


