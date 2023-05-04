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

    from cashflower import assign, ModelVariable, Constant

    from tutorials.asset.bond.input import main, runplan, assumption

    t_end = Constant()
    cal_month = ModelVariable(mp_dep=False)
    cal_year = ModelVariable(mp_dep=False)
    coupon = ModelVariable()
    nominal_value = ModelVariable()
    present_value = ModelVariable()


    @assign(t_end)
    def _t_end():
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


    @assign(coupon)
    def _coupon(t):
        if t != 0 and t <= t_end() and cal_month(t) == main.get("issue_month"):
            return main.get("nominal") * main.get("coupon_rate")
        else:
            return 0


    @assign(nominal_value)
    def _nominal_value(t):
        if t == t_end():
            return main.get("nominal")
        else:
            return 0


    @assign(present_value)
    def _present_value(t):
        i = assumption["INTEREST_RATE"]
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
It is modelled as a constant because it's time-independent.
:code:`t_end` will be used for the nominal value's formula.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable, Constant

    from tutorials.asset.bond.input import main, runplan, assumption

    t_end = Constant()

    @assign(t_end)
    def _t_end():
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

Calendar year and month have the same values for all policyholders.
So the :code:`mp_dep` parameter (model point dependent) can be set to :code:`False` to improve runtime.
The valuation year and month are read from the runplan.

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

**Coupon**

Each year, the investor receives a coupon. It is calculated by multiplying the nominal value and the coupon rate.

..  code-block:: python
    :caption: model.py

    coupon = ModelVariable()

    @assign(coupon)
    def _coupon(t):
        if t != 0 and t <= t_end() and cal_month(t) == main.get("issue_month"):
            return main.get("nominal") * main.get("coupon_rate")
        else:
            return 0

|

**Nominal value**

At the end of the term, the investor receives back the nominal.

..  code-block:: python
    :caption: model.py

    nominal_value = ModelVariable()

    @assign(nominal_value)
    def _nominal_value(t):
        if t == t_end():
            return main.get("nominal")
        else:
            return 0


|

**Present value**

Cash flows are discounted with the interest rate read from assumptions to calculate the present value.

..  code-block:: python
    :caption: model.py

    present_value = ModelVariable()

    @assign(present_value)
    def _present_value(t):
        i = assumption["INTEREST_RATE"]
        return coupon(t) + nominal_value(t) + present_value(t+1) * (1/(1+i))**(1/12)

|

Results
^^^^^^^

..  code-block::
    :caption: <timestamp>_main.csv

      t  r  cal_month  cal_year  coupon  nominal_value  present_value  t_end
      0  1       12.0    2022.0     0.0            0.0    1100.670155    114
      1  1        1.0    2023.0     0.0            0.0    1102.488002    114
      2  1        2.0    2023.0     0.0            0.0    1104.308850    114
      3  1        3.0    2023.0     0.0            0.0    1106.132706    114
      4  1        4.0    2023.0     0.0            0.0    1107.959574    114
      5  1        5.0    2023.0     0.0            0.0    1109.789460    114
      6  1        6.0    2023.0    30.0            0.0    1111.622367    114
      7  1        7.0    2023.0     0.0            0.0    1083.408754    114
      8  1        8.0    2023.0     0.0            0.0    1085.198092    114
      9  1        9.0    2023.0     0.0            0.0    1086.990385    114
     10  1       10.0    2023.0     0.0            0.0    1088.785638    114
     11  1       11.0    2023.0     0.0            0.0    1090.583856    114
     12  1       12.0    2023.0     0.0            0.0    1092.385044    114
     13  1        1.0    2024.0     0.0            0.0    1094.189206    114
     14  1        2.0    2024.0     0.0            0.0    1095.996349    114
     15  1        3.0    2024.0     0.0            0.0    1097.806476    114
     16  1        4.0    2024.0     0.0            0.0    1099.619593    114
     17  1        5.0    2024.0     0.0            0.0    1101.435704    114
     18  1        6.0    2024.0    30.0            0.0    1103.254814    114
     19  1        7.0    2024.0     0.0            0.0    1075.027382    114
    ...
    113  1        5.0    2032.0     0.0            0.0    1028.301676    114
    114  1        6.0    2032.0    30.0         1000.0    1030.000000    114

Notes:
    * :code:`coupon` - coupon is paid each year. The bond has been issued 6 months before that valuation date so the first payment is in the sixth month of the projection. The second payment is after 12 months.
    * :code:`nominal_value` - the investor receives back the nominal at the end of the term (:code:`t=114`).
    * :code:`present_value` - present value at the beginning of the projection is higher than the nominal because the coupon rate is higher than the interest rate.
