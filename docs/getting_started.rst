Getting started
===============

Quick start
-----------

Cashflower is an open-source Python framework for actuarial cash flow models.

|

Prerequisities
^^^^^^^^^^^^^^

To use cashflower, you need Python version :code:`>=3.9`.

|

Installation
^^^^^^^^^^^^

Cashflower is available on python Package Index (PyPI). You can install it with the :code:`pip` tool.

..  code-block::
    :caption: terminal

    pip install cashflower

|

Create model
^^^^^^^^^^^^

Start your project with creating a new model. You can create multiple models for each product that you work on.
Pass on the name when creating the model, e.g. :code:`wol`.

..  code-block:: python
    :caption: python

    from cashflower import create_model

    create_model("wol")

The :code:`create_model()` function creates an initial structure of the model.

..  code-block::

    .
    ├── input.py
    ├── model.py
    ├── run.py
    └── settings.py

The initial structure consists of the :code:`input.py`, :code:`model.py`, :code:`run.py` and :code:`settings.py` scripts.

|

Input
^^^^^

In the :code:`input.py` script, you can define your model point sets and assumptions.

.. code-block:: python
   :caption: wol/input.py

    import pandas as pd

    from cashflower import Runplan, ModelPointSet

    runplan = Runplan(data=pd.DataFrame({
        "version": [1],
        "valuation_year": [2022],
        "valuation_month": [12]
    }))

    main = ModelPointSet(data=pd.read_csv("C:/my_data/policy.csv"))

    assumption = dict()
    assumption["interest_rates"] = pd.read_csv("C:/my_data/interest_rates.csv")
    assumption["mortality"] = pd.read_csv("C:/my_data/mortality.csv", index_col="age")

Runplan bases on the :code:`Runplan` class, model point sets base on the :code:`ModelPointSet` class and assumptions have a form of a dictionary.

|

Model
^^^^^

The :code:`model.py` script contains the logic of the model. You can define model variables and assign formulas to them.

.. code-block:: python
   :caption: wol/model.py

    from cashflower import assign, ModelVariable

    age = ModelVariable(model_point_set=main)
    death_prob = ModelVariable(model_point_set=main)

    @assign(age)
    def _age(t):
        if t == 0:
            return int(main.get("AGE"))
        elif t % 12 == 0:
            return age(t-1) + 1
        else:
            return age(t-1)


    @assign(death_prob)
    def _death_prob(t):
        if age(t) == age(t-1):
            return death_prob(t-1)
        elif age(t) <= 100:
            sex = main.get("SEX")
            yearly_rate = assumption["mortality"].loc[age(t)][sex]
            monthly_rate = (1 - (1 - yearly_rate)**(1/12))
            return monthly_rate
        else:
            return 1

The variables defined in :code:`model.py` will be calculated and saved in the output.

|

Calculate
^^^^^^^^^

To calculate the model, run :code:`run.py`.

..  code-block::
    :caption: terminal

    cd wol
    python run.py

This command will create the model's output.

|

Model overview
--------------

Actuarial models help to predict future cash flows of insurance products.

The main components of an actuarial model are:
    * model point sets,
    * assumptions,
    * runplan,
    * model's components: model variables and constants,
    * results.

.. image:: https://acturtle.com/static/img/17/cash-flow-model-overview.webp

**Run plan** - run plan is a list of runs that we want to perform with the model.

**Model point sets** - points of data for which the model is calculated.
For example, a model point can contain policyholder's attributes such as age, sex, premiums, coverage, etc.
Model point sets can be split into separate files.
For example, there might be separate files for fund and coverage data.

**Assumptions** - actuarial models are calculated based on assumptions.
Examples of underwriting assumptions include mortality, lapses or expenses.
Market assumptions are, for example, interest rates curves.
Assumptions are also product's parameters, such as fees or levels of guarantees.

**Model** - actuarial model reminds a spider's web. There are many variables which dependent on each other.

We can distinguish between two types of variables:

* model variables - time-dependent - variables that depend on the projection's period (e.g. present value of premiums),
* constants - time-independent - variables that stay the same for the whole projection (e.g. gender of the policyholder).

**Results** - the output of the calculation logic.

|

Time
----

Actuarial cash flow models try to predict the future. The results are put on a timeline with future dates.
Time variable :code:`t` plays an import role.

|

Timeline
^^^^^^^^

Timeline starts at zero (:code:`t=0`) which is the valuation period.
If the reporting period is the end of year 2021, then :code:`t=0` is 2021-12-31.

The :code:`t` variable reflects certain **point** in time. The projections are monthly so:
    * :code:`t=1` is 2022-01-31,
    * :code:`t=2` is 2022-02-28,
    * :code:`t=3` is 2022-03-31,
    * ...

.. image:: https://acturtle.com/static/img/20/timeline.webp

|

Periods
^^^^^^^

Some components of the model concern **periods** rather than points in time.
In these cases, the :code:`t` variable has a different meaning.

.. WARNING::
   The :code:`t` variable might mean a point in time as well as a period.

For example, interest rates curve helps to calculate the value of money in time.
If the monthly rate amounts to :code:`0.1%` then €100.00 at the end of February is worth €100.10 at the end of March.

The assumption can be presented in the following way:

=====  =====
t      rate
=====  =====
...    ...
3      0.001
...    ...
=====  =====

The rate is applied to a third period.

.. image:: https://acturtle.com/static/img/20/timeline-with-periods.webp

|

Moment in month
^^^^^^^^^^^^^^^

By default, :code:`t` reflects the end of the month.
If cash flows in different moments of the month, it can be reflected using discounting.

.. TIP::
   Use the right discounting if the cash flow does not happen at the end of the month.

For example, there are premiums occurring **in the middle of** the month.

Then use if interest rate is :code:`i`, use :code:`(1/(1+i))**(1/2)` for discounting.
