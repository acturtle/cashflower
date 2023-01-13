Whole life
==========

The whole life insurance is a contract between a policyholder and an insurance company.
The policyholder pays premiums to the insurance company.
In exchange, the insurer pays a benefit on policyholder's death.

Solution
--------

In this model, we will calculate best estimate liabilities.

See the full solution below and a more detailed explanation later on.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.whole_life.input import policy, assumption


    age = ModelVariable()
    death_prob = ModelVariable()
    survival_rate = ModelVariable()
    expected_premium = ModelVariable()
    expected_benefit = ModelVariable()
    projection_year = ModelVariable(pol_dep=False)
    yearly_spot_rate = ModelVariable(pol_dep=False)
    yearly_forward_rate = ModelVariable(pol_dep=False)
    forward_rate = ModelVariable(pol_dep=False)
    discount_rate = ModelVariable(pol_dep=False)
    pv_expected_premium = ModelVariable()
    pv_expected_benefit = ModelVariable()
    best_estimate_liabilities = ModelVariable()


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


    @assign(expected_premium)
    def expected_premium_formula(t):
        premium = policy.get("premium")
        return premium * survival_rate(t-1)


    @assign(expected_benefit)
    def expected_benefit_formula(t):
        sum_assured = policy.get("sum_assured")
        return survival_rate(t-1) * death_prob(t) * sum_assured


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


    @assign(pv_expected_premium)
    def pv_expected_premium_formula(t):
        return expected_premium(t) + pv_expected_premium(t+1) * discount_rate(t+1)


    @assign(pv_expected_benefit)
    def pv_expected_benefit_formula(t):
        return expected_benefit(t) + pv_expected_benefit(t+1) * discount_rate(t+1)


    @assign(best_estimate_liabilities)
    def best_estimate_liabilities_formula(t):
        return pv_expected_benefit(t) - pv_expected_premium(t)

|

Description
-----------

Create model :code:`whole_life`.

..  code-block:: python
    :caption: python console

    from cashflower import create_model

    create_model("whole_life")

|

Input
^^^^^

The model will be calculated for two model points.

..  code-block:: python
    :caption: input.py

    policy = ModelPoint(data=pd.DataFrame({
        "policy_id": ["a", "b"],
        "age": [32, 40],
        "sex": ["male", "female"],
        "sum_assured": [100_000, 80_000],
        "premium": [140, 110]
    }))

The first policyholder is a 32-year-old man who pays premiums of 140 and is assured for 100 000.
The second policyholder is a 40-year-old woman who pays premiums of 110 and is assured for 80 000.

|

The model bases on two sets of assumptions: interest rates and mortality rates.

..  code-block:: python
    :caption: input.py

    assumption = dict()
    assumption["mortality"] = pd.read_csv("./input/mortality.csv")
    assumption["interest_rates"] = pd.read_csv("./input/interest_rates.csv")


Mortality rates are split by age and sex.

..  code-block::
    :caption: mortality.csv

    age,male,female
    0,0.00389,0.00315
    1,0.00028,0.00019
    2,0.00019,0.00014
    3,0.00015,0.00011
    4,0.00012,0.00009
    5,0.0001,0.00008
    ...
    30,0.00135,0.00035
    31,0.00144,0.00038
    32,0.00155,0.00042
    33,0.00167,0.00046
    34,0.00179,0.00051
    35,0.00193,0.00057
    ...
    40,0.00276,0.0009
    41,0.00299,0.00099
    42,0.00326,0.00109
    43,0.00356,0.0012
    44,0.0039,0.00133
    45,0.00429,0.00148
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
^^^^^


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

**expected_premium**

The premium will be paid only if the policyholder survives.

..  code-block:: python

    @assign(expected_premium)
    def expected_premium_formula(t):
        premium = policy.get("premium")
        return premium * survival_rate(t-1)

|

**expected_benefit**

The benefit will be paid out if the policyholder survives until the beginning of the period and dies within the period.

..  code-block:: python

    @assign(expected_benefit)
    def expected_benefit_formula(t):
        sum_assured = policy.get("sum_assured")
        return survival_rate(t-1) * death_prob(t) * sum_assured

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

**pv_expected_premium**

The present value of expected premiums is the value of all future premiums as of today.

..  code-block:: python

    @assign(pv_expected_premium)
    def pv_expected_premium_formula(t):
        return expected_premium(t) + pv_expected_premium(t+1) * discount_rate(t+1)

|

**pv_expected_benefit**

The current value of the expected benefit.

..  code-block:: python

    @assign(pv_expected_benefit)
    def pv_expected_benefit_formula(t):
        return expected_benefit(t) + pv_expected_benefit(t+1) * discount_rate(t+1)

|

**best_estimate_liabilities**

The best estimate of liabilities is the sum the present value of outflows less the present value of inflows.

..  code-block:: python

    best_estimate_liabilities = ModelVariable()

    @assign(best_estimate_liabilities)
    def best_estimate_liabilities_formula(t):
        return pv_expected_benefit(t) - pv_expected_premium(t)

|

Results
^^^^^^^

To run the model, source :code:`run.py`.

..  code-block::
    :caption: terminal

    cd whole_life
    python run.py

The individual results calculated by the model for the first 13 months:

..  code-block::
    :caption: <timestamp>_policy.csv

    t,r,age,best_estimate_liabilities,death_prob,discount_rate,expected_benefit,expected_premium,forward_rate,projection_year,pv_expected_benefit,pv_expected_premium,survival_rate,yearly_forward_rate,yearly_spot_rate
    0,1,32,-6559.33,0.000129,1.0,0.0,0.0,0.0,0,36967.2,43526.53,0.999871,0.0,0.0
    1,1,32,-6566.21,0.000129,0.998952,12.9,139.98,0.001049,1,37005.98,43572.19,0.999742,0.01266,0.01266
    2,1,32,-6445.88,0.000129,0.998952,12.9,139.96,0.001049,1,37031.89,43477.77,0.999613,0.01266,0.01266
    3,1,32,-6325.45,0.000129,0.998952,12.9,139.95,0.001049,1,37057.83,43383.28,0.999484,0.01266,0.01266
    4,1,32,-6204.91,0.000129,0.998952,12.89,139.93,0.001049,1,37083.79,43288.7,0.999355,0.01266,0.01266
    5,1,32,-6084.25,0.000129,0.998952,12.89,139.91,0.001049,1,37109.79,43194.04,0.999226,0.01266,0.01266
    6,1,32,-5963.48,0.000129,0.998952,12.89,139.89,0.001049,1,37135.82,43099.3,0.999097,0.01266,0.01266
    7,1,32,-5842.6,0.000129,0.998952,12.89,139.87,0.001049,1,37161.88,43004.48,0.998968,0.01266,0.01266
    8,1,32,-5721.62,0.000129,0.998952,12.89,139.86,0.001049,1,37187.96,42909.58,0.998839,0.01266,0.01266
    9,1,32,-5600.52,0.000129,0.998952,12.89,139.84,0.001049,1,37214.07,42814.59,0.99871,0.01266,0.01266
    10,1,32,-5479.31,0.000129,0.998952,12.88,139.82,0.001049,1,37240.21,42719.52,0.998581,0.01266,0.01266
    11,1,32,-5357.98,0.000129,0.998952,12.88,139.8,0.001049,1,37266.39,42624.37,0.998452,0.01266,0.01266
    12,1,33,-5236.55,0.000139,0.998952,13.88,139.78,0.001049,1,37292.59,42529.14,0.998313,0.01266,0.01266
    13,1,33,-5117.55,0.000139,0.998652,13.88,139.76,0.00135,2,37329.03,42446.58,0.998174,0.016323,0.01449
    0,1,40,-5171.13,7.5e-05,1.0,0.0,0.0,0.0,0,29274.34,34445.47,0.999925,0.0,0.0
    1,1,40,-5176.56,7.5e-05,0.998952,6.0,109.99,0.001049,1,29305.05,34481.61,0.99985,0.01266,0.01266
    2,1,40,-5077.89,7.5e-05,0.998952,6.0,109.98,0.001049,1,29329.79,34407.68,0.999775,0.01266,0.01266
    3,1,40,-4979.13,7.5e-05,0.998952,6.0,109.98,0.001049,1,29354.55,34333.68,0.9997,0.01266,0.01266
    4,1,40,-4880.26,7.5e-05,0.998952,6.0,109.97,0.001049,1,29379.34,34259.6,0.999625,0.01266,0.01266
    5,1,40,-4781.3,7.5e-05,0.998952,6.0,109.96,0.001049,1,29404.16,34185.46,0.99955,0.01266,0.01266
    6,1,40,-4682.25,7.5e-05,0.998952,6.0,109.95,0.001049,1,29429.0,34111.25,0.999475,0.01266,0.01266
    7,1,40,-4583.1,7.5e-05,0.998952,6.0,109.94,0.001049,1,29453.87,34036.97,0.9994,0.01266,0.01266
    8,1,40,-4483.86,7.5e-05,0.998952,6.0,109.93,0.001049,1,29478.76,33962.62,0.999325,0.01266,0.01266
    9,1,40,-4384.52,7.5e-05,0.998952,6.0,109.93,0.001049,1,29503.68,33888.2,0.99925,0.01266,0.01266
    10,1,40,-4285.08,7.5e-05,0.998952,6.0,109.92,0.001049,1,29528.63,33813.71,0.999175,0.01266,0.01266
    11,1,40,-4185.55,7.5e-05,0.998952,6.0,109.91,0.001049,1,29553.6,33739.15,0.9991,0.01266,0.01266
    12,1,41,-4085.92,8.3e-05,0.998952,6.63,109.9,0.001049,1,29578.6,33664.52,0.999017,0.01266,0.01266
    13,1,41,-3988.02,8.3e-05,0.998652,6.63,109.89,0.00135,2,29611.89,33599.91,0.998934,0.016323,0.01449


Few things to note:
    * age - we have read the age for t=0 from the model point and derived age for remaining periods,
    * death_prob - we read probability of death from assumptions based on age,
    * survival_rate - that's the probability that the policyholder will survive from the beginning of the projection to the given t, so it changes each month,
    * expected_premium - the policyholder pays €140 each month but the company will receive the premium only when the policyholder survives, the expected premium decreases with time,
    * expected_benefit - the policyholder will receive €100 000 in case of death, the expected benefit assumes that the policyholder survived up to the certain period and then died,
    * discount_rate - we have modelled few variables to then derive discount rate which are used to calculate the present value of cash flows,
    * pv_expected_premium - that's the current value of all future expected premiums,
    * pv_expected_benefit - that's the current value of all future expected benefits,
    * best_estimate_liabilities - negative BEL implies that the product is profitable at the given moment.
