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

Model point independent
^^^^^^^^^^^^^^^^^^^^^^^

The model variables are recalculated for each of the model points.
The default value for the :code:`mp_dep` (model point dependent) parameter of :code:`ModelVariable` is :code:`True`.

If the results for the given variable are the same for all model points, the parameter :code:`mp_dep` should be set
to :code:`False`. This setting helps to decrease the runtime of the model.

|

Variable A: model point dependent

..  code-block:: python

    ModelVariable()

or

..  code-block:: python

    ModelVariable(mp_dep=True)

Variable B: model point independent

..  code-block:: python

    ModelVariable(mp_dep=False)

|

**Comparison**

.. image:: https://acturtle.com/static/img/31/graph.png
   :align: center

In the above image we see that:

* A - variable changes for each of the model points,
* B - variable has the same results for all model points.

|

**Example**

Variables:

* :code:`pv_premiums` - the present value of premiums differs by policyholder,
* :code:`calendar_month` - calendar month is the same for all policyholders.

..  code-block:: python
    :caption: model.py

    pv_premiums = ModelVariable()
    calendar_month = ModelVariable(mp_dep=False)


    @assign(pv_premiums)
    def pv_premiums_formula(t):
        v = 1/(1+0.001)
        return premium(t) + pv_premiums(t+1) * v


    @assign(calendar_month)
    def calendar_month_formula(t):
        valuation_month = 6
        if t == 0:
            return valuation_month
        elif calendar_month(t - 1) % 12 == 1:
            return 1
        else:
            return calendar_month(t - 1) + 1


Calendar month can have the :code:`mp_dep` attribute set to :code:`False` because the results are the same for all
model points.

|

Constant
--------

Constant is a **t-independent** component of the model.

Create constant
^^^^^^^^^^^^^^^

..  code-block:: python
    :caption: model.py

    from cashflower import assign, Constant

    premium = Constant()

    @assign(premium)
    def premium_formula():
        return main.get("PREMIUM")

There are two steps to define a constant:
    #. Create an instance of the :code:`Constant` class.
    #. Assign a formula to the variable.

The first step is to create a variable, which is an instance of the :code:`Constant` class.

..  code-block:: python

    premium = Constant()

The second step is to use the decorator :code:`@assign()` to link a formula to the variable.

:code:`@assign()` takes as an argument a constant.

..  code-block:: python

    @assign(premium)


Constants can be numbers or strings. Strings can not be summed up so constants can not be part of the aggregated output.

Constants are part of the model output only if the model outputs individual results.

.. IMPORTANT::
    Constants are part of the output report only if the :code:`AGGREGATE` setting is set to :code:`False`.

|

Formula
^^^^^^^

For constants, :code:`@assign()` decorates the function without any parameters.

.. IMPORTANT::
    The formula of the constant can not have any parameters.

The function contains the logic for the constant variable.

..  code-block:: python

    def premium_formula():
        return main.get("PREMIUM")

Constants may return numeric or character values.

|

Time independent
^^^^^^^^^^^^^^^^

The :code:`Constant` class is used to code time-independent model components.
Time-independent variables have the same result for :code:`t=0`, :code:`t=1`, :code:`t=2`, ...

|

Variable A: time-dependent

..  code-block:: python

    ModelVariable()

Variable B: time-independent

..  code-block:: python

    Constant()

|

**Comparison**

.. image:: https://acturtle.com/static/img/34/graph.png
   :align: center

In the above image we see that:

* A - variable has different results between periods,
* B - variable has the same result for all periods.

|

**Example**

Variables:

* :code:`pv_premiums` - the present value of premiums differs by time,
* :code:`premium` - premium is the same for all periods.


..  code-block:: python
    :caption: model.py

    pv_premiums = ModelVariable()
    premium = Constant()

    @assign(pv_premiums)
    def pv_premiums_formula(t):
        v = 1/(1+0.001)
        return premium(t) + pv_premiums(t+1) * v

    @assign(premium)
    def premium_formula():
        return main.get("PREMIUM")

Premium can be coded as an instance of the :code:`Constant` class because it is time-independent.
Its formula does not require the :code:`t` parameter.

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

.. IMPORTANT::
    To use results of :code:`a`, call :code:`a()` and **not** :code:`a_formula()`.

If you are calling a model variable, pass an argument :code:`t`.

A variable can also call **itself** for other :code:`t`. This functionality can be useful for discounting.

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

Link to model point set
-----------------------

Model variables and constants are associated with a model point set.

To link a model point set with a model component, use the :code:`model_point_set` parameter of the class.
If a model point set is not set explicitly, it will be set to :code:`main` by default.

|

The default model point set is :code:`main`:

..  code-block:: python

    ModelVariable()

is equivalent to

..  code-block:: python

    ModelVariable(model_point_set=main)

|

To use a different model point set, it should be in the :code:`model_point_set` parameter explicitly.

..  code-block:: python
    :caption: model.py

    from my_model.input import main, fund

    mortality_rate = ModelVariable(model_point_set=main)
    fund_value = ModelVariable(model_point_set=fund)

|

To read from a model point, use the :code:`get()` method of the :code:`ModelPointSet` class.

..  code-block:: python

    main.get("age")

The :code:`get()` method will retrieve value from the currently calculated model point.

..  code-block:: python
    :caption: model.py

    from my_model.input import fund

    fund_value = ModelVariable(model_point_set=fund)


    @assign(fund_value)
    def fund_formula(t):
        if t == 0:
            return fund.get("fund_value")
        return fund_value(t-1) * 1.02

|

The model will create a separate output file for each of the model point sets:

..  code-block::

    .
    └── output/
        ├── <timestamp>_main.csv
        └── <timestamp>_fund.csv

The output files will contain results for model components linked to an associated model point set.
