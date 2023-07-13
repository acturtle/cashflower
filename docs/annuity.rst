Annuity
=======

A life annuity is a series of payments while a given life survives.

Life annuities play a major role in life insurance. Life insurances are usually purchased by a life annuity of premiums rather than by a single premium.
The amount payable at the time of claim may be converted through a settlement option into some form of life annuity for the beneficiary.

Annuities are also central in pension systems as our retirements have a form of an annuity.
They also have a role in disability and workers' compensation insurances.

A life annuity may be termporary, that is, limited to a given term of years, or it may be payable for the whole of life.
The payments may commence immediately or the annuity may be deferred.

Payments may be due at the beginnings of the payment intervals (annuitites-due) or at the ends of such intervals (annuities-immediate).

There are multiple types of life annuities. We will build simple models to illustrate the mechanism behind:

* a whole life annuity
* an n-year temporary life annuity
* an m-year deferred whole life annuity

|

**Actuarial present value**

In our models, we will calculate the actuarial present value of life annuities.

The table below presents the usual actuarial notation for the actuarial present value of life annuities.

.. image:: https://acturtle.com/static/img/docs/notation-annuity.jpg


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
    * :code:`expected_payment`,
    * :code:`actuarial_present_value`.

The :code:`survival_rate` and the :code:`actuarial_present_value` are calculated in the same way for all types of life
insurance.

..  code-block:: python

    @variable()
    def survival_rate(t):
        if t == 0:
            return 1
        return survival_rate(t-1) * (1 - DEATH_PROB)

The survival rate is the probability that the policyholder will survive from the beginning of the projection until the :code:`t` time.

..  code-block:: python

    @variable(actuarial_present_value)
    def actuarial_present_value(t):
        if t == settings["T_MAX_CALCULATION"]:
            return expected_payment(t)
        return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)

The actuarial present value is **the present value** of the expected annuity payments.
The discount rate is calculated as :code:`1/(1+INTEREST_RATE)`.


Whole life annuity
------------------

Whole life annuity provides a policyholder with a periodic (e.g. monthly) payments as long as the policyholder lives.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import ModelPointSet

    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "payment": [1_000]
    }))

Policy data contains the value of the monthly payment which is be paid to the policyholder.

..  code-block:: python
    :caption: model.py

    from cashflower import variable

    from tutorials.annuity.whole_life.input import main
    from tutorials.annuity.whole_life.settings import settings

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    @variable()
    def survival_rate(t):
        if t == 0:
            return 1
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @variable()
    def expected_payment(t):
        if t == 0:
            return 0
        return survival_rate(t) * main.get("payment")


    @variable()
    def actuarial_present_value(t):
        if t == settings["T_MAX_CALCULATION"]:
            return expected_payment(t)
        return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)

The policyholder will receive a payment as long as they survive.

|

Temporary life annuity
----------------------

An n-year temporary life annuity provides a policyholder with a periodic (e.g. monthly) payments for n years.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import Runplan, ModelPointSet


    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "payment": [1_000],
        "remaining_term": [36],
    }))


Policy data contains the value of the monthly payment and the remaining term of the annuity.
Here the remaining term is expressed in months starting the valuation period (rather than the issue date).

..  code-block:: python
    :caption: model.py

    from cashflower import variable

    from tutorials.annuity.temporary.input import main
    from tutorials.annuity.temporary.settings import settings

    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    @variable()
    def survival_rate(t):
        if t == 0:
            return 1
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @variable()
    def expected_payment(t):
        if t == 0 or t > main.get("remaining_term"):
            return 0
        return survival_rate(t) * main.get("payment")


    @variable()
    def actuarial_present_value(t):
        if t == settings["T_MAX_CALCULATION"]:
            return expected_payment(t)
        return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)

The policyholder will receive a payment as long as they survive but no longer than n-years.

|

Deferred whole life annuity
---------------------------

An m-year deferred whole life annuity provides a policyholder with a periodic (e.g. monthly) payments as long as the policyholder lives starting m years after the issue.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    from cashflower import Runplan, ModelPointSet


    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "payment": [1_000],
        "deferral": [12],
    }))


Policy data contains the value of the monthly payment which is be paid to the policyholder and the deferral period.
Here the deferral period is expressed in months starting from the valuation period (rather than the issue date).

..  code-block:: python
    :caption: model.py

    from cashflower import variable

    from tutorials.annuity.deferred.input import main
    from tutorials.annuity.deferred.settings import settings


    INTEREST_RATE = 0.005
    DEATH_PROB = 0.003

    @variable()
    def survival_rate(t):
        if t == 0:
            return 1
        return survival_rate(t-1) * (1 - DEATH_PROB)


    @variable()
    def expected_payment(t):
        if t <= main.get("deferral"):
            return 0
        return survival_rate(t) * main.get("payment")


    @variable()
    def actuarial_present_value(t):
        if t == settings["T_MAX_CALCULATION"]:
            return expected_payment(t)
        return expected_payment(t) + actuarial_present_value(t+1) * 1/(1+INTEREST_RATE)

The policyholder will receive a payment as long as they survive starting m-years after the issue date.

|
