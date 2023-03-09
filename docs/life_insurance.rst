Life insurance
==============

Life insurance aims to reduce the financial impact of the event of untimely death.
The life insurances are long-term in nature which provides a significant element of uncertainty.

The size and time of payment in life insurance depend on the time of death of the insured.
The actuarial cash flow models are built as a function of the :code:`t` variable.

We usually consider life insurance as insurance on human lives, but the same idea can apply to objects, such as: equipment, machines or loans.

There are multiple types of life insurance. We will build simple models to illustrate the mechanism behind:

* level benefit insurance

  * a whole life insurance
  * an n-year term life insurance
* endowment insurance

  * an n-year pure endowment
  * an n-year endowment insurance
* deferred insurance

|

**Net single premium**

In our models, we will calculate the net single premium.

The present value of the benefit payment is a random variable.
The expectation of this variable at policy issue is called the net single premium. It is:

* a **net** premium because it does not contain any risk loading (a risk loading is compensation for taking the variability risk),
* a **single** premium in contrast to monthly, annual or other premiums that are acceptable in life insurance practice.

The table below presents the actuarial notation for the net single premium.

.. image:: https://acturtle.com/static/img/docs/notation-life-insurance.jpg

|

Common variables
----------------

For simplicity, we will use monthly constant mortality and interest rate.

..  code-block:: python
    :caption: model.py

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

In the production actuarial cash flow models:
    * mortality rates depend on the age and the sex of the policyholder,
    * interest rates are a curve and vary for each future period.

It's also usual that assumptions contain yearly data that must be converted into monthly rates within the model.
The examples below are simplified to focus on the calculation of the expected benefit.

The common variables in the models are:
    * :code:`survival_rate`,
    * :code:`exepcted_benefit`,
    * :code:`net_single_premium`.

The :code:`survival_rate` and the :code:`net_single_premium` are calculated in the same way for all types of life
insurance.

..  code-block:: python

    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - DEATH_PROB
        return survival_rate(t-1) * (1-DEATH_PROB)

The survival rate is the probability that the policyholder will survive from the beginning of the projection until the :code:`t` time.

..  code-block:: python

    @assign(net_single_premium)
    def net_single_premium_formula(t):
        return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)

The net single premium is **the present value** of the expected benefit payments.
The discount rate is calculated as :code:`1/(1+INTEREST_RATE)`.

|

Level benefit insurance
-----------------------

Whole life
^^^^^^^^^^

Whole life insurance provides for payment following the death of the insured at any time in the future.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPointSet

    policy = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "sum_assured": [100_000]
    }))

The policy data contains the sum assured which will be paid to the policyholder's designated person in case of death.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.life_insurance.whole_life.input import policy

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    survival_rate = ModelVariable()
    expected_benefit = ModelVariable()
    net_single_premium = ModelVariable()

    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - DEATH_PROB
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @assign(expected_benefit)
    def expected_benefit_formula(t):
        sum_assured = policy.get("sum_assured")
        if t == 1200:
            return survival_rate(t-1) * sum_assured
        return survival_rate(t-1) * DEATH_PROB * sum_assured


    @assign(net_single_premium)
    def net_single_premium_formula(t):
        return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)


The policyholder's designated person will receive the sum assured when the policyholder dies in the :code:`t` period.

The whole life insurance lasts until the death of the policyholder.
Our projection lasts :code:`1200` months, so we have assumed that the probability of death amounts to 1 in the last period.

In the production actuarial models, the mortality assumptions are usually up to the age of 120
and assume that the mortality rate is 1 (100%) for the last year.

|

Term life
^^^^^^^^^

An n-year term life insurance provides a payment only if the insured dies within the n-year term of an insurance
commencing at issue.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPointSet

    policy = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "sum_assured": [100_000],
        "remaining_term": [36],
    }))

The policy data contains the sum assured and the term of the insurance.
In our case, the term is expressed as the remaining term (starting from the valuation period) in months.

The policy data may alternatively contain the term from the policy's issue date (rather than the valuation period)
and in years (rather than months).
In that case, the actuary should develop additional variables or adjust the existing ones.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.life_insurance.term_life.input import policy

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    survival_rate = ModelVariable()
    expected_benefit = ModelVariable()
    net_single_premium = ModelVariable()


    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - DEATH_PROB
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @assign(expected_benefit)
    def expected_benefit_formula(t):
        if t > policy.get("remaining_term"):
            return 0
        return survival_rate(t-1) * DEATH_PROB * policy.get("sum_assured")


    @assign(net_single_premium)
    def net_single_premium_formula(t):
        return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)

The person designated by the policyholder will receive the sum assured if the policyholder dies within the term.

|

Endowment insurance
-------------------

Pure endowment
^^^^^^^^^^^^^^

An n-year pure endowment provides for a payment at the end of the n years if and only if the insured survives at least
n-years from the time of the policy issue.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPointSet

    policy = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "sum_assured": [100_000],
        "remaining_term": [36],
    }))

The policy data contains the sum assured and the term of the insurance.
In our case, the term is expressed as the remaining term (starting from the valuation period) in months.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.life_insurance.pure_endowment.input import policy

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    survival_rate = ModelVariable()
    expected_benefit = ModelVariable()
    net_single_premium = ModelVariable()


    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - DEATH_PROB
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @assign(expected_benefit)
    def expected_benefit_formula(t):
        if t == policy.get("remaining_term"):
            return survival_rate(t) * policy.get("sum_assured")
        return 0


    @assign(net_single_premium)
    def net_single_premium_formula(t):
        return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)


The policyholder will receive the sum assured if they survive until the end of the term.

Endowment
^^^^^^^^^

N-year endowment insurance provides for an amount to be payable either following the death of the insured or upon
the survival of the insured to the end of the n-year term, whichever occurs first.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPointSet

    policy = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "sum_assured": [100_000],
        "remaining_term": [36],
    }))

The policy data contains the sum assured and the term of the insurance.
In our case, the term is expressed as the remaining term (so starting from the valuation) in months.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.life_insurance.pure_endowment.input import policy

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    survival_rate = ModelVariable()
    expected_benefit = ModelVariable()
    net_single_premium = ModelVariable()


    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - DEATH_PROB
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @assign(expected_benefit)
    def expected_benefit_formula(t):
        sum_assured = policy.get("sum_assured")
        remaining_term = policy.get("remaining_term")

        if t < remaining_term:
            return survival_rate(t-1) * DEATH_PROB * sum_assured
        elif t == remaining_term:
            return survival_rate(t) * sum_assured
        else:
            return 0


    @assign(net_single_premium)
    def net_single_premium_formula(t):
        return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)


The policyholder receives a sum assured either when they die within the term or if they survive until the end of the term.
Notice that the endowment insurance can be seen as the term life insurance plus pure endowment.


Deferred insurance
------------------

An m-year deferred insurance provides for a benefit following the death of the insured only if the insured dies
at least m years following policy issue.


..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPointSet


    policy = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "sum_assured": [100_000],
        "deferral": [24],
    }))


The policy data contain the sum assured and the deferral period.
In our case, the deferral period is expressed starting from the valuation period and is the number of months.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    from tutorials.life_insurance.whole_life.input import policy

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    survival_rate = ModelVariable()
    expected_benefit = ModelVariable()
    net_single_premium = ModelVariable()


    @assign(survival_rate)
    def survival_rate_formula(t):
        if t == 0:
            return 1 - DEATH_PROB
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @assign(expected_benefit)
    def expected_benefit_formula(t):
        if t < policy.get("deferral"):
            return 0
        return survival_rate(t-1) * DEATH_PROB * policy.get("sum_assured")


    @assign(net_single_premium)
    def net_single_premium_formula(t):
        return expected_benefit(t) + net_single_premium(t+1) * 1/(1+INTEREST_RATE)

The policyholder receives the sum assured if they die after the deferral period.
