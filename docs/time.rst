Time
====

The time variable (:code:`t`) is a system variable in actuarial cash flow models.
The :code:`t` variable represents monthly periods starting from zero.

The model is run for the valuation date chosen by the actuary.
The valuation date reflects the start of the model (:code:`t=0`).
The information on the valuation date can be stored in the runplan.

.. image:: https://acturtle.com/static/img/docs/timeline.png

Below you can find model formulas for time-related variables that might be helpful in the model's development.

|

Solution
--------

Formulas:

..  code-block:: python
    :caption: model.py

    import math
    from cashflower import assign, ModelVariable, Constant

    from tutorials.time.input import main, runplan

    cal_month = ModelVariable(mp_dep=False)
    cal_year = ModelVariable(mp_dep=False)
    elapsed_months = Constant()
    pol_month = ModelVariable()
    pol_year = ModelVariable()


    @assign(cal_month)
    def _cal_month(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1


    @assign(cal_year)
    def _cal_year(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)


    @assign(elapsed_months)
    def _elapsed_months():
        issue_year = main.get("issue_year")
        issue_month = main.get("issue_month")
        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


    @assign(pol_month)
    def _pol_month(t):
        if t == 0:
            mnth = elapsed_months() % 12
            mnth = 12 if mnth == 0 else mnth
            return mnth
        if pol_month(t-1) == 12:
            return 1
        return pol_month(t-1) + 1


    @assign(pol_year)
    def _pol_year(t):
        if t == 0:
            return math.floor(elapsed_months() / 12)
        if pol_month(t) == 1:
            return pol_year(t-1) + 1
        return pol_year(t-1)


Input:

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import Runplan, ModelPointSet


    runplan = Runplan(data=pd.DataFrame({
        "version": [1],
        "valuation_year": [2022],
        "valuation_month": [12]
    }))


    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "issue_year": [2020],
        "issue_month": [6],
    }))




Description
-----------

|

Input
^^^^^

Model uses runplan to store the information on the valuation date.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import Runplan, ModelPointSet


    runplan = Runplan(data=pd.DataFrame({
        "version": [1],
        "valuation_year": [2022],
        "valuation_month": [12]
    }))

The policyholder has a policy that was issued in June 2020.

..  code-block:: python
    :caption: input.py

    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "issue_year": [2020],
        "issue_month": [6],
    }))

|

Model
^^^^^

**Calendar year and month**

Knowing the valuation date, we can calculate actual calendar years and months.
These variables have the same values for all policyholders.
So the :code:`mp_dep` parameter (model point dependent) can be set to :code:`False`.
The valuation year and month can be read from the runplan.

..  code-block:: python
    :caption: model.py

    cal_month = ModelVariable(mp_dep=False)
    cal_year = ModelVariable(mp_dep=False)

    @assign(cal_month)
    def _cal_month(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1


    @assign(cal_year)
    def _cal_year(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)


|

**Elapsed months**

Each policy starts at a different moment. The policy's issue date might be part of the model points.
Elapsed months reflect how many months have passed between the policy's issue and the valuation date.
Elapsed months is time-independent so can be modelled as a :code:`Constant`.

..  code-block:: python
    :caption: model.py

    elapsed_months = Constant()

    @assign(elapsed_months)
    def _elapsed_months():
        issue_year = main.get("issue_year")
        issue_month = main.get("issue_month")
        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)

|

**Policy year and month**

Policy year and month reflect the duration of the given policy.

..  code-block:: python
    :caption: model.py

    pol_month = ModelVariable()
    pol_year = ModelVariable()

    @assign(pol_month)
    def _pol_month(t):
        if t == 0:
            mnth = elapsed_months() % 12
            mnth = 12 if mnth == 0 else mnth
            return mnth
        if pol_month(t-1) == 12:
            return 1
        return pol_month(t-1) + 1


    @assign(pol_year)
    def _pol_year(t):
        if t == 0:
            return math.floor(elapsed_months() / 12)
        if pol_month(t) == 1:
            return pol_year(t-1) + 1
        return pol_year(t-1)

|

Results
^^^^^^^

The result for the first 13 months.

..  code-block::
    :caption: <timestamp>_main.csv

    t,cal_year,cal_month,elapsed_months,pol_year,pol_month
    0,2022,12,30,2,6
    1,2023,1,30,2,7
    2,2023,2,30,2,8
    3,2023,3,30,2,9
    4,2023,4,30,2,10
    5,2023,5,30,2,11
    6,2023,6,30,2,12
    7,2023,7,30,3,1
    8,2023,8,30,3,2
    9,2023,9,30,3,3
    10,2023,10,30,3,4
    11,2023,11,30,3,5
    12,2023,12,30,3,6
    13,2024,1,30,3,7

Notes:
    * :code:`cal_month`, :code:`cal_year` - starts with valuation date,
    * :code:`elapsed_months` - number of months between issue of the policy (2020-06) and the valuation date (2022-12),
    * :code:`pol_month`, :code:`pol_year` - the policy was already 2 years and 6 months "old" at the valuation date.
