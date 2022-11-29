Annuity
=======

Solution
--------

See the full solution below and a more detailed explanation later on.

In this model, we calculate the present value of annuity payments.

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
            yearly_rate = assumption["mortality"].loc[age(t)][sex]
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
        "age": [65, 50],
        "sex": ["female", "male"],
        "payment": [1750, 1000]
    }))


The first policyholder is a 65-year-old woman who receives monthly annuity payment of 1750.

A second policyholder is a 50-year-old man who receives payment of 1000.

|

The model uses two assumptions: interest rates and mortality rates.

..  code-block:: python
    :caption: input.py

    assumption = dict()
    assumption["mortality"] = pd.read_csv("./input/mortality.csv")
    assumption["interest_rates"] = pd.read_csv("./input/interest_rates.csv")


Mortality rates are split by age and sex.

..  code-block::
    :caption: mortality.csv

    age,male,female
    ...
    30,0.00135,0.00035
    31,0.00144,0.00038
    32,0.00155,0.00042
    33,0.00167,0.00046
    34,0.00179,0.00051
    35,0.00193,0.00057
    ...
    65,0.02714,0.01142
    66,0.02941,0.01252
    67,0.03177,0.01375
    68,0.03417,0.0151
    69,0.03665,0.01662
    70,0.03925,0.01829
    ...

Interest rates are dependent on the projection year.

..  code-block::
    :caption: interest_rates.csv

    t,value
    1,0.00736
    2,0.01266
    3,0.01449
    4,0.0161
    5,0.01687
    6,0.01782
    7,0.01863
    8,0.01942
    9,0.02017
    10,0.02089
    11,0.02178
    12,0.02207
    ...

|

Model
-----

**age**

At the beginning of the projection, :code:`age` is read from the policy data and then increased by 1 every 12 months.
We need age to read the corresponding mortality rate.

..  code-block:: python

    age = ModelVariable()

    @assign(age)
    def age_formula(t):
        if t == 0:
            return int(policy.get("age"))
        elif t % 12 == 0:
            return age(t-1) + 1
        else:
            return age(t-1)

|

**death_prob**

The probability of death is read from assumptions for the given age and gender.
The yearly rate is transformed into a monthly rate.
If the age does not change from the previous period, the model returns the same mortality rate.
There are no available data above the age of 100, so the rate amounts to 1.

..  code-block:: python

    death_prob = ModelVariable()

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

|

**survival_rate**

The survival rate is the probability that the policyholder survived until the end of the period.
The probability of death concerns one month.
The survival rate concerns the period from the beginning of the projection until the given period.

..  code-block:: python

    survival_rate = ModelVariable()

    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - death_prob(t)
        else:
            return survival_rate(t-1) * (1 - death_prob(t))

|

**projection_year**

The projection year is needed to read the corresponding interest rate.
The results are the same for all policyholders so the argument :code:`pol_dep` is set to :code:`False`.

..  code-block:: python

    projection_year = ModelVariable(pol_dep=False)

    @assign(projection_year)
    def projection_year_formula(t):
        if t == 0:
            return 0
        elif t % 12 == 1:
            return projection_year(t - 1) + 1
        else:
            return projection_year(t - 1)

|

**yearly_spot_rate**

A yearly spot rate is read from the assumption file.

..  code-block:: python

    yearly_spot_rate = ModelVariable(pol_dep=False)

    @assign(yearly_spot_rate)
    def yearly_spot_rate_formula(t):
        if t == 0:
            return 0
        else:
            return assumption["interest_rates"].loc[projection_year(t)]["value"]

|

**yearly_forward_rate**

From the spot rates, we derive forward rates which are used for period-by-period calculations.

..  code-block:: python

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


|

**forward_rate**

The model has a monthly frequency, so the yearly rates are converted into monthly ones.

..  code-block:: python

    @assign(forward_rate)
    def forward_rate_formula(t):
        return (1+yearly_forward_rate(t))**(1/12)-1

|

**discount_rate**

To calculate the present value of future cash flows, we need discount rates.

..  code-block:: python

    @assign(discount_rate)
    def discount_rate_formula(t):
        return 1/(1+forward_rate(t))

|

**expected_payment**

The policyholder that has an annuity will receive payments only if they survive.
The expected annuity payment takes into account the survival rate.

..  code-block:: python

    @assign(expected_payment)
    def expected_payment_formula(t):
        payment = policy.get("payment")
        return payment * survival_rate(t-1)

|

**pv_expected_payment**

The present value of expected payments is the value of all future payments as of today.

..  code-block:: python

    @assign(pv_expected_payment)
    def pv_expected_payment_formula(t):
        return expected_payment(t) + pv_expected_payment(t+1) * discount_rate(t+1)

|

Results
-------

To run the model, source :code:`run.py`.

..  code-block::
    :caption: terminal

    cd annuity
    python run.py


The individual results calculated by the model for the first 13 months:

..  code-block::
    :caption: <timestamp>_policy.csv

    t,r,age,death_prob,discount_rate,expected_payment,forward_rate,projection_year,pv_expected_payment,survival_rate,yearly_forward_rate,yearly_spot_rate
    0,1,65,0.000957,1.0,0.0,0.0,0,318218.96,0.999043,0.0,0.0
    1,1,65,0.000957,0.998952,1748.33,0.001049,1,318552.8,0.998087,0.01266,0.01266
    2,1,65,0.000957,0.998952,1746.65,0.001049,1,317136.83,0.997132,0.01266,0.01266
    3,1,65,0.000957,0.998952,1744.98,0.001049,1,315721.06,0.996178,0.01266,0.01266
    4,1,65,0.000957,0.998952,1743.31,0.001049,1,314305.47,0.995225,0.01266,0.01266
    5,1,65,0.000957,0.998952,1741.64,0.001049,1,312890.07,0.994273,0.01266,0.01266
    6,1,65,0.000957,0.998952,1739.98,0.001049,1,311474.86,0.993321,0.01266,0.01266
    7,1,65,0.000957,0.998952,1738.31,0.001049,1,310059.82,0.99237,0.01266,0.01266
    8,1,65,0.000957,0.998952,1736.65,0.001049,1,308644.97,0.99142,0.01266,0.01266
    9,1,65,0.000957,0.998952,1734.98,0.001049,1,307230.3,0.990471,0.01266,0.01266
    10,1,65,0.000957,0.998952,1733.32,0.001049,1,305815.81,0.989523,0.01266,0.01266
    11,1,65,0.000957,0.998952,1731.67,0.001049,1,304401.5,0.988576,0.01266,0.01266
    12,1,66,0.001049,0.998952,1730.01,0.001049,1,302987.36,0.987539,0.01266,0.01266
    13,1,66,0.001049,0.998652,1728.19,0.00135,2,301663.99,0.986503,0.016323,0.01449
    0,1,50,0.000585,1.0,0.0,0.0,0,225019.67,0.999415,0.0,0.0
    1,1,50,0.000585,0.998952,999.42,0.001049,1,225255.74,0.99883,0.01266,0.01266
    2,1,50,0.000585,0.998952,998.83,0.001049,1,224491.59,0.998246,0.01266,0.01266
    3,1,50,0.000585,0.998952,998.25,0.001049,1,223727.23,0.997662,0.01266,0.01266
    4,1,50,0.000585,0.998952,997.66,0.001049,1,222962.64,0.997078,0.01266,0.01266
    5,1,50,0.000585,0.998952,997.08,0.001049,1,222197.84,0.996495,0.01266,0.01266
    6,1,50,0.000585,0.998952,996.5,0.001049,1,221432.82,0.995912,0.01266,0.01266
    7,1,50,0.000585,0.998952,995.91,0.001049,1,220667.58,0.995329,0.01266,0.01266
    8,1,50,0.000585,0.998952,995.33,0.001049,1,219902.13,0.994747,0.01266,0.01266
    9,1,50,0.000585,0.998952,994.75,0.001049,1,219136.46,0.994165,0.01266,0.01266
    10,1,50,0.000585,0.998952,994.16,0.001049,1,218370.56,0.993583,0.01266,0.01266
    11,1,50,0.000585,0.998952,993.58,0.001049,1,217604.45,0.993002,0.01266,0.01266
    12,1,51,0.000645,0.998952,993.0,0.001049,1,216838.12,0.992362,0.01266,0.01266
    13,1,51,0.000645,0.998652,992.36,0.00135,2,216136.47,0.991722,0.016323,0.01449

Few things to note:
    * expected_payment - the annuity payment will be paid only if the policyholder survives up to the payment,
    * pv_expected_payment - the expected present value of annuity payments is a liability to the insurance company.
