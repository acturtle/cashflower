Model
=====

The logic of the model is defined in the :code:`model.py` script.

The components of the model are :code:`ModelVariable` and :code:`Constant`.
Model variable depends on time and the constant doesn't.
By default, they depend on the model point but this can be changed using the :code:`mp_dep` attribute.

.. image:: https://acturtle.com/static/img/31/all.png
   :align: center

|

Defining model variables and constants:

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable, Constant

    premium = Constant()
    pv_premium = ModelVariable()


    @assign(premium)
    def _premium():
        return 100


    @assign(pv_premium)
    def _pv_premium(t):
        return pv_premium(t+1) * (1/1.05) + premium()

|

Model variable
--------------

The model variable is the main building block of the actuarial cash flow model.
The model variable depends on time (:code:`t`) and returns numeric values.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    pv_premium = ModelVariable()

    @assign(pv_premium)
    def _pv_premium(t):
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

For model variables, :code:`@assign()` decorates the function with the parameter :code:`t`.

.. IMPORTANT::
    The formula of the model variable must have only one parameter :code:`t`.

The function contains the logic for the calculation. The name of the function is not relevant.
It's a good practice to name the function the same as the model component with the underscore as prefix (:code:`_myvariable(t)`).

..  code-block:: python

    def _pv_premium(t):
        return pv_premium(t+1) * (1/1.05) + 100

Model variables return numeric values.

|

Constant
--------

The constant is a **t-independent** component of the model.
The constant can return either a numeric value or a string.
Constants can be only part of an individual output because strings can't be aggregated.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, Constant

    premium = Constant()

    @assign(premium)
    def _premium():
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

For constants, :code:`@assign()` decorates the function without any parameters.

.. IMPORTANT::
    The formula of the constant can not have any parameters.

The function contains the logic for the constant variable. The name of the function is not relevant.
It's a good practice to name the function the same as the model component with the underscore as prefix (:code:`_myconstant()`).

..  code-block:: python

    def _premium():
        return main.get("PREMIUM")

Constants may return numeric or character values.

|


Parameters
----------

model_point_set
^^^^^^^^^^^^^^^

Model variables and constants are associated with a model point set.

To link a model point set with a model component, use the :code:`model_point_set` parameter of the class.
If a model point set is not set explicitly, it will be set to :code:`main` by default.

|

The default model point set is :code:`main`:

..  code-block:: python

    ModelVariable()

...is equivalent to...

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
    def _fund_value(t):
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


mp_dep
^^^^^^

The model variables are recalculated for each of the model points.
The default value for the :code:`mp_dep` (model point dependent) parameter of :code:`ModelVariable` is :code:`True`.

If the results for the given variable are the same for all model points, the parameter :code:`mp_dep` should be set
to :code:`False`. This setting helps to decrease the runtime of the model.

|

**Model Variable**

.. image:: https://acturtle.com/static/img/31/model_variable.png
   :align: center

In the above image, we see that:

* MV_1 - variable returns different results for each of the model points,
* MV_2 - variable returns the same results for all model points.

To steer if a variable is model point dependent, use the :code:`mp_dep` attribute of the :code:`ModelVariable` class.

MV_1: model point dependent

..  code-block:: python

    ModelVariable()

...is the same as...

..  code-block:: python

    ModelVariable(mp_dep=True)

|

MV_2: model point independent

..  code-block:: python

    ModelVariable(mp_dep=False)

|

Example

Variables:

* :code:`pv_premiums` - the present value of premiums differs by policyholder,
* :code:`calendar_month` - calendar month is the same for all policyholders.

..  code-block:: python
    :caption: model.py

    pv_premiums = ModelVariable()
    calendar_month = ModelVariable(mp_dep=False)


    @assign(pv_premiums)
    def _pv_premiums(t):
        v = 1/(1+0.001)
        return premium(t) + pv_premiums(t+1) * v


    @assign(calendar_month)
    def _calendar_month(t):
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

**Constant**

Similarly to model variables, constants can also be model point independent.

.. image:: https://acturtle.com/static/img/31/constant.png
   :align: center

In the above image we see that:

* C_1 - there are the same results for all periods but they differ between model points,
* C_2 - there are the same results for all periods and model points.


..  code-block:: python
    :caption: model.py

    premium = Constant()
    product = Constant(mp_dep=False)


    @assign(premium)
    def _premium():
        return main.get("PREMIUM")


    @assign(product)
    def _product():
        return "ANNUITY"


Calling results
---------------

Model components can be called in each other formulas.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable, Constant

    a = Constant()
    b = ModelVariable()
    c = ModelVariable()


    @assign(a)
    def _a():
        return 100


    @assign(b)
    def _b(t):
        return 3*t + a()


    @assign(c)
    def _c(t):
        return b(t) + 1

To use another variable, call an instance of the :code:`ModelVariable` or :code:`Constant` class.

.. IMPORTANT::
    To use results of :code:`a`, call :code:`a()` and **not** :code:`_a()`.

If you are calling a model variable, pass an argument :code:`t`.

A variable can also call **itself** for other :code:`t`. This functionality can be useful for discounting.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    d = ModelVariable()

    @assign(d)
    def _d(t):
        if t == 1200:
            return 100
        return d(t+1) * (1/1.05)

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