Model
=====

The logic of the model is defined in the :code:`model.py` script.

The components of the model are :code:`ModelVariable` and :code:`Constant`.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable, Constant

    premium = Constant()
    pv_premium = ModelVariable()


    @assign(premium)
    def premium_formula():
        return 100


    @assign(pv_premium)
    def pv_premium_formula(t):
        return pv_premium(t+1) * (1/1.05) + premium()

|

Model variable
--------------

Model variable is the main building block of the actuarial cash flow model.

Create model variable
^^^^^^^^^^^^^^^^^^^^^

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

    pv_premium = ModelVariable()

The second step is to use the decorator :code:`@assign()` to link a formula to the variable.

:code:`@assign()` takes as an argument a model variable.

..  code-block:: python

    @assign(pv_premium)

|

Formula
^^^^^^^

For model variables, :code:`@assign()` decorates the function with the parameter :code:`t`.

.. IMPORTANT::
    The formula of the model variable must have only one parameter :code:`t`.

The function contains the logic for the calculation.

..  code-block:: python

    def pv_premium_formula(t):
        return pv_premium(t+1) * (1/1.05) + 100

Model variables return numeric values.

|

Constant
--------

Constant is a t-independent component of the model.

Create constant
^^^^^^^^^^^^^^^

..  code-block:: python
    :caption: model.py

    from cashflower import assign, Constant

    premium = Constant()

    @assign(premium)
    def premium_formula(t):
        return policy.get("PREMIUM")

There are two steps to define a constant:
    #. Create an instance of the :code:`Constant` class.
    #. Assign a formula to the variable.

The first step is to create a variable, which is an instance of the :code:`Constant` class.

..  code-block:: python

    premium = Constant()

The second step is to use the decorator :code:`@assign()` to link a formula to the variable.

:code:`@assign()` takes as an argument a parameter.

..  code-block:: python

    @assign(premium)

|

Formula
^^^^^^^

For constants, :code:`@assign()` decorates the function without any parameters.

.. IMPORTANT::
    The formula of the constant can not have any parameters.

The function contains the logic for the constant variable.

..  code-block:: python

    def premium_formula(t):
        return policy.get("PREMIUM")

Constants may return numeric and character values.

|

Comparison
----------

:code:`ModelVariable` and :code:`Constant` are the main components of the model.

The components differ in two areas:

* dependency on time,
* output type.

The table presents the differences:

.. list-table::
   :widths: 33 33 33
   :header-rows: 1

   * - Characteristic
     - ModelVariable
     - Constant
   * - is time-dependent
     - Yes
     - No
   * - returns numbers
     - Yes
     - Yes
   * - returns strings
     - No
     - Yes

|

Calling variables
-----------------

Model components can be called in each other formulas.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable, Constant

    a = Constant()
    b = ModelVariable()
    c = ModelVariable()


    @assign(a)
    def a_formula():
        return 100


    @assign(b)
    def b_formula(t):
        return 3*t + a()


    @assign(c)
    def c_formula(t):
        return b(t) + 1

To use another variable, call an instance of the :code:`ModelVariable` or :code:`Constant` class.

If you are calling a model variable, pass an argument :code:`t`.

.. IMPORTANT::
    To use results of :code:`a`, call :code:`a()` and **not** :code:`a_formula()`.

A variable can also call **itself**. This functionality can be useful for discounting.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    d = ModelVariable()

    @assign(d)
    def d_formula(t):
        if t == 1200:
            return 100
        return d(t+1) * (1/1.05)

|

Link to model point
-------------------

Model variables and constants are associated with a model point.

To link a model point with a model component, use the :code:`modelpoint` parameter of the class.
If a model point is not set explicitly, it will be set to :code:`policy` by default.

|

The default model point is :code:`policy`:

..  code-block:: python

    ModelVariable()

is equivalent to

..  code-block:: python

    ModelVariable(modelpoint=policy)

|

To use a different model point, it should be set to the :code:`modelpoint` parameter explicitly.

..  code-block:: python
    :caption: model.py

    from my_model.input import policy, fund

    mortality_rate = ModelVariable(modelpoint=policy)
    fund_value = ModelVariable(modelpoint=fund)

|

To read from a model point, use the :code:`get()` method of the :code:`ModelPoint` class.

..  code-block:: python

    policy.get("age")

The :code:`get()` method will retrieve value from the currently evaluated policy.

..  code-block:: python
    :caption: model.py

    from my_model.input import fund

    fund_value = ModelVariable(modelpoint=fund)


    @assign(fund_value)
    def fund_formula(t):
        if t == 0:
            return fund.get("fund_value")
        return fund_value(t-1) * 1.02

|

The model will create a separate output file for each of the model points:

..  code-block::

    .
    └── output/
        ├── <timestamp>_policy.csv
        └── <timestamp>_fund.csv

The output files will contain results for model components linked to an associated model point.
