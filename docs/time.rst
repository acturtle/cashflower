Time-related variables
======================

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

    from tutorials.time.input import policy, runplan

    cal_month = ModelVariable(modelpoint=policy, pol_dep=False)
    cal_year = ModelVariable(modelpoint=policy, pol_dep=False)
    elapsed_months = Constant(modelpoint=policy)
    pol_month = ModelVariable(modelpoint=policy)
    pol_year = ModelVariable(modelpoint=policy)


    @assign(cal_month)
    def cal_month_formula(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1


    @assign(cal_year)
    def cal_year_formula(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)


    @assign(elapsed_months)
    def elapsed_months_formula():
        issue_year = policy.get("issue_year")
        issue_month = policy.get("issue_month")
        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


    @assign(pol_month)
    def pol_month_formula(t):
        if t == 0:
            mnth = elapsed_months() % 12
            mnth = 12 if mnth == 0 else mnth
            return mnth
        if pol_month(t-1) == 12:
            return 1
        return pol_month(t-1) + 1


    @assign(pol_year)
    def pol_year_formula(t):
        if t == 0:
            return math.floor(elapsed_months() / 12)
        if pol_month(t) == 1:
            return pol_year(t-1) + 1
        return pol_year(t-1)


Input:

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import Runplan, ModelPoint


    runplan = Runplan(data=pd.DataFrame({
        "version": [1],
        "valuation_year": [2022],
        "valuation_month": [12]
    }))


    policy = ModelPoint(data=pd.DataFrame({
        "policy_id": [1],
        "issue_year": [2020],
        "issue_month": [6],
    }))




Description
-----------

Calendar year and month
^^^^^^^^^^^^^^^^^^^^^^^

Knowing the valuation date, we can calculate actual calendar years and months.
These variables have the same values for all policyholders.
So the :code:`pol_dep` parameter (policy-dependent) can be set to :code:`False`.
The valuation year and month can be read from the runplan.

..  code-block:: python
    :caption: model.py

    cal_month = ModelVariable(modelpoint=policy, pol_dep=False)
    cal_year = ModelVariable(modelpoint=policy, pol_dep=False)

    @assign(cal_month)
    def cal_month_formula(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1


    @assign(cal_year)
    def cal_year_formula(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)


Elapsed months
^^^^^^^^^^^^^^

Each policy starts at a different moment. The policy's issue date might be part of the model points.
Elapsed months reflect how many months have passed between the policy's issue and the valuation date.
Elapsed months is time-independent so can be modelled as a :code:`Constant`.

..  code-block:: python
    :caption: model.py

    elapsed_months = Constant(modelpoint=policy)

    @assign(elapsed_months)
    def elapsed_months_formula():
        issue_year = policy.get("issue_year")
        issue_month = policy.get("issue_month")
        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (valuation_year - issue_year) * 12 + (valuation_month - issue_month)


Policy year and month
^^^^^^^^^^^^^^^^^^^^^

Policy year and month reflect the duration of the given policy.

..  code-block:: python
    :caption: model.py

    @assign(pol_month)
    def pol_month_formula(t):
        if t == 0:
            mnth = elapsed_months() % 12
            mnth = 12 if mnth == 0 else mnth
            return mnth
        if pol_month(t-1) == 12:
            return 1
        return pol_month(t-1) + 1


    @assign(pol_year)
    def pol_year_formula(t):
        if t == 0:
            return math.floor(elapsed_months() / 12)
        if pol_month(t) == 1:
            return pol_year(t-1) + 1
        return pol_year(t-1)

