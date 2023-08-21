Bond
====

A bond is a type of financial asset that represents a loan made by an investor to a borrower, typically a company or a government.
When an investor buys a bond, they are essentially lending money to the borrower in exchange for regular coupon payments
and a promise to repay the initial amount (nominal) at a future date, known as the bond's maturity date.

Bonds come in different types and are typically issued with a fixed coupon rate, which is determined at the time of issuance.
The coupon payments are usually made periodically, such as monthly or annually,
and the amount paid is determined by the coupon rate and the nominal.

Bonds are often considered a relatively safe investment because they are backed by the borrower's ability to repay the loan,
and they offer a fixed rate of return.
However, the value of bonds can also fluctuate based on changes in interest rates and market conditions.

In the tutorial, we will build a model for a 10-year bond with an annual coupon.

.. image:: https://acturtle.com/static/img/38/bond.png

At the beginning, the investor pays nominal value to the borrower.
The borrower pays coupons to the investor for 10 consecutive years.
At the end of the term, the borrower returns the nominal to the investor.

|

Solution
--------

Formulas:

..  code-block:: python
    :caption: model.py

    from cashflower import variable
    from input import main, runplan, assumption
    from settings import settings


    @variable()
    def t_end():
        years = main.get("term") // 12
        months = main.get("term") - years * 12

        end_year = main.get("issue_year") + years
        end_month = main.get("issue_month") + months

        if end_month > 12:
            end_year += 1
            end_month -= 12

        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (end_year - valuation_year) * 12 + (end_month - valuation_month)


    @variable()
    def cal_month(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1


    @variable()
    def cal_year(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)


    @variable()
    def coupon(t):
        if t != 0 and t <= t_end(t) and cal_month(t) == main.get("issue_month"):
            return main.get("nominal") * main.get("coupon_rate")
        else:
            return 0


    @variable()
    def nominal_value(t):
        if t == t_end():
            return main.get("nominal")
        else:
            return 0


    @variable()
    def present_value(t):
        i = assumption["INTEREST_RATE"]
        if t == settings["T_MAX_CALCULATION"]:
            return coupon(t) + nominal_value(t)
        return coupon(t) + nominal_value(t) + present_value(t+1) * (1/(1+i))**(1/12)


Input:

..  code-block:: python
    :caption: input.py

    import pandas as pd
    from cashflower import Runplan, ModelPointSet


    runplan = Runplan(data=pd.DataFrame({
        "version": [1],
        "valuation_year": [2022],
        "valuation_month": [12],
    }))


    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "nominal": [1000],
        "coupon": [0.03],
        "term": [120],
        "issue_year": [2022],
        "issue_month": [6],
    }))


    assumption = dict()
    assumption["INTEREST_RATE"] = 0.02


Description
-----------

|

Input
^^^^^

The model uses runplan to store the information on the valuation date.

..  code-block:: python
    :caption: input.py

    import pandas as pd
    from cashflower import Runplan, ModelPointSet


    runplan = Runplan(data=pd.DataFrame({
        "version": [1],
        "valuation_year": [2022],
        "valuation_month": [12],
    }))


The bond has a nominal value of €1000 and a coupon rate of 3%. The term of the bond amounts to 120 months (10 years).
It has been issued in June 2022.

..  code-block:: python
    :caption: input.py

    main = ModelPointSet(data=pd.DataFrame({
        "id": [1],
        "nominal": [1000],
        "coupon": [0.03],
        "term": [120],
        "issue_year": [2022],
        "issue_month": [6],
    }))

The interest rate is constant and amounts to 2%.

..  code-block:: python
    :caption: input.py

    assumption = dict()
    assumption["INTEREST_RATE"] = 0.02

|

Model
^^^^^

**End month**

The number of months between the valuation date and the end of the bond.

..  code-block:: python
    :caption: model.py

    from cashflower import variable
    from input import main, runplan, assumption
    from settings import settings

    @variable()
    def t_end(t):
        years = main.get("term") // 12
        months = main.get("term") - years * 12

        end_year = main.get("issue_year") + years
        end_month = main.get("issue_month") + months

        if end_month > 12:
            end_year += 1
            end_month -= 12

        valuation_year = runplan.get("valuation_year")
        valuation_month = runplan.get("valuation_month")
        return (end_year - valuation_year) * 12 + (end_month - valuation_month)

|

**Calendar year and month**

The valuation year and month are read from the runplan.

..  code-block:: python
    :caption: model.py

    @variable()
    def cal_month(t):
        if t == 0:
            return runplan.get("valuation_month")
        if cal_month(t-1) == 12:
            return 1
        else:
            return cal_month(t-1) + 1


    @variable()
    def cal_year(t):
        if t == 0:
            return runplan.get("valuation_year")
        if cal_month(t-1) == 12:
            return cal_year(t-1) + 1
        else:
            return cal_year(t-1)

|

**Coupon**

Each year, the investor receives a coupon. It is calculated by multiplying the nominal value and the coupon rate.

..  code-block:: python
    :caption: model.py

    @variable()
    def coupon(t):
        if t != 0 and t <= t_end() and cal_month(t) == main.get("issue_month"):
            return main.get("nominal") * main.get("coupon_rate")
        else:
            return 0

|

**Nominal value**

At the end of the term, the investor receives back the nominal.

..  code-block:: python
    :caption: model.py

    @variable()
    def nominal_value(t):
        if t == t_end():
            return main.get("nominal")
        else:
            return 0


|

**Present value**

Cash flows are discounted with the interest rate read from assumptions to calculate the present value.

..  code-block:: python
    :caption: model.py

    @variable()
    def present_value(t):
        i = assumption["INTEREST_RATE"]
        if t == settings["T_MAX_CALCULATION"]:
            return coupon(t) + nominal_value(t)
        return coupon(t) + nominal_value(t) + present_value(t+1) * (1/(1+i))**(1/12)

|
