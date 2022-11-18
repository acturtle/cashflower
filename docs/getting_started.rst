Getting started
===============

Quick start
-----------

Cashflower is an open-source Python framework for actuarial cash flow models.

|

**Prerequisities**

To use cashflower, you need Python version :code:`>=3.9`.

|

**Installation**

Cashflower is available on python Package Index (PyPI). You can install it with the :code:`pip` tool.

..  code-block::
    :caption: terminal

    pip install cashflower

|

**Create model**

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

**Input**

In the :code:`input.py` script, you can define your model points and assumptions.

.. code-block:: python
   :caption: wol/input.py

    policy = ModelPoint(data=pd.read_csv("C:/my_data/policy.csv"))

    assumption = dict()
    assumption["interest_rates"] = pd.read_csv("C:/my_data/interest_rates.csv")
    assumption["mortality"] = pd.read_csv("C:/my_data/mortality.csv", index_col="age")

Model points base on the :code:`ModelPoint` class and assumptions have a form of a dictionary.

|

**Model**

The :code:`model.py` script contains the logic of the model. You can define model variables and assign formulas to them.

.. code-block:: python
   :caption: wol/model.py

    age = ModelVariable(modelpoint=policy)
    death_prob = ModelVariable(modelpoint=policy)

    @assign(age)
    def age_formula(t):
        if t == 0:
            return int(policy.get("AGE"))
        elif t % 12 == 0:
            return age(t-1) + 1
        else:
            return age(t-1)


    @assign(death_prob)
    def death_prob_formula(t):
        if age(t) == age(t-1):
            return death_prob(t-1)
        elif age(t) <= 100:
            sex = policy.get("SEX")
            yearly_rate = assumption["mortality"].loc[age(t)][sex]
            monthly_rate = (1 - (1 - yearly_rate)**(1/12))
            return monthly_rate
        else:
            return 1

The variables defined in :code:`model.py` will be evaluated and saved in the output.

|

**Calculate**

To calculate variables for model points, run :code:`run.py`.

..  code-block::
    :caption: terminal

    cd wol
    python run.py

This command will create the model's output.

|

Cash flow model overview
------------------------

Actuarial models help to predict future cash flows of insurance products.

The main components of an actuarial model are:
    * model points (policy data),
    * assumptions,
    * run plan,
    * model's components: model variables and parameters,
    * results.

.. image:: https://acturtle.com/static/img/17/cash-flow-model-overview.webp

**Run plan** - run plan is a list of runs that we want to perform with the model.

**Model points** - policyholders' data such as age, sex, premiums, coverage, etc.
Model points can be split into separate files.
For example, there might be separate files for fund and coverage data.

**Assumptions** - actuarial models are calculated based on assumptions.
Examples of underwriting assumptions include mortality, lapses or expenses.
Market assumptions are, for example, interest rates curves.
Assumptions are also product's parameters, such as fees or levels of guarantees.

**Model** - actuarial model reminds a spider's web. There are many variables which dependent on each other.

We can distinguish between two types of variables:

* model variables - time-dependent - variables that depend on the projection's period (e.g. present value of premiums),
* parameters - time-independent - variables that stay the same for the whole projection (e.g. gender of the policyholder).

**Results** - the output of the calculation logic.
