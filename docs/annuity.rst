Annuity
=======

Solution
--------

See model solution below and the more detailed explanation later on.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.annuity.input import policy, assumption


    age = ModelVariable()
    death_prob = ModelVariable()
    survival_rate = ModelVariable()
    projection_year = ModelVariable(pol_dep=False)
    yearly_spot_rate = ModelVariable(pol_dep=False)
    yearly_forward_rate = ModelVariable(pol_dep=False)
    forward_rate = ModelVariable(pol_dep=False)
    discount_rate = ModelVariable(pol_dep=False)
    expected_payment = ModelVariable()
    pv_expected_payment = ModelVariable()


    @assign(age)
    def age_formula(t):
        if t == 0:
            return int(policy.get("age"))
        elif t % 12 == 0:
            return age(t-1) + 1
        else:
            return age(t-1)


    @assign(death_prob)
    def death_prob_formula(t):
        sex = policy.get("sex")
        if age(t) == age(t-1):
            return death_prob(t-1)
        elif age(t) <= 100:
            yearly_rate = float(assumption["mortality"].loc[age(t)][sex])
            monthly_rate = (1 - (1 - yearly_rate)**(1/12))
            return monthly_rate
        else:
            return 1


    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - death_prob(t)
        else:
            return survival_rate(t-1) * (1 - death_prob(t))


    @assign(projection_year)
    def projection_year_formula(t):
        if t == 0:
            return 0
        elif t % 12 == 1:
            return projection_year(t - 1) + 1
        else:
            return projection_year(t - 1)


    @assign(yearly_spot_rate)
    def yearly_spot_rate_formula(t):
        if t == 0:
            return 0
        else:
            return assumption["interest_rates"].loc[projection_year(t)]["value"]


    @assign(yearly_forward_rate)
    def yearly_forward_rate_formula(t):
        if t == 0:
            return 0
        elif t == 1:
            return yearly_spot_rate(t)
        elif t % 12 != 1:
            return yearly_forward_rate(t-1)
        else:
            return ((1+yearly_spot_rate(t))**projection_year(t))/((1+yearly_spot_rate(t-1))**projection_year(t-1)) - 1


    @assign(forward_rate)
    def forward_rate_formula(t):
        return (1+yearly_forward_rate(t))**(1/12)-1


    @assign(discount_rate)
    def discount_rate_formula(t):
        return 1/(1+forward_rate(t))


    @assign(expected_payment)
    def expected_payment_formula(t):
        payment = policy.get("payment")
        return payment * survival_rate(t-1)


    @assign(pv_expected_payment)
    def pv_expected_payment_formula(t):
        return expected_payment(t) + pv_expected_payment(t+1) * discount_rate(t+1)


|

Input
-----

In model points, there are two policies.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPoint

    policy = ModelPoint(data=pd.DataFrame({
        "policy_id": ["a", "b"],
        "age": [65, 30],
        "sex": ["female", "male"],
        "payment": [1750, 1000]
    }))


The first policyholder is a 65-years-old woman who pays 1750.
The second policyholder is a 30-years-old man whose payment amounts to 1000.

|

Model uses two assumptions: interest rates and mortality rates.

..  code-block:: python
    :caption: input.py

    assumption = dict()
    assumption["mortality"] = pd.read_csv("./input/mortality.csv")
    assumption["interest_rates"] = pd.read_csv("./input/interest_rates.csv")


Mortality rates are split by age and sex.


