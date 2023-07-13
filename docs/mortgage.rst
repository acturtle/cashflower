Mortgage
========

A real estate mortgage is a loan from the bank to the customer that must be used to purchase real estate.
The amount borrowed is typically large and the term is long (usually between 15 and 30 years).
The payment frequency of real estate mortgages is almost always on a monthly basis.

Let's define:
    * :code:`L` - the value of the loan,
    * :code:`R` - the monthly payment on the loan,
    * :code:`i` - annual rate of interest on the loan,
    * :code:`j` - the monthly rate of interest on the loan (equal to :code:`i/12`).

The customer pays the same amount every month for the given term, so we can use an annuity certain (:code:`ann`).

The bank pays the value of the loan to the customer now.
The customer pays the monthly payments over a certain period.

The most important equation is that these two values must equal:

..  code-block:: python

    L = R * ann

Let's recall that:

..  code-block:: python

    ann = (1 - v ** n)/j

The bank is earning on this contract by setting the interest rate high enough.

Modelling
---------

|

Input
^^^^^

Let's build an amortization schedule for a €100 000 real estate mortgage with monthly payments
at 10% interest convertible monthly and a term of 30 years.

We will put this information into the model point set.

..  code-block:: python
    :caption: model.py

    main = ModelPointSet(data=pd.DataFrame({
      "id": [1],
      "loan": [100_000],
      "interest_rate": [0.1],
      "term": [360]
    }))

|

Model
^^^^^

In the model point set, we have the value of the yearly interest rate, so let's create a variable for a monthly interest rate.
The rate does not change value from month to month so it's a time-independent variable.
The function has no :code:`t` parameter.

..  code-block:: python
    :caption: model.py

    @variable()
    def monthly_interest_rate():
        return main.get("interest_rate") / 12

The monthly rate is the yearly rate divided by 12.

Now we need to determine the value of the regular monthly payment.

..  code-block:: python
    :caption: model.py

    @variable()
    def payment():
        L = main.get("loan")
        n = main.get("term")
        j = monthly_interest_rate()
        v = 1 / (1 + j)
        ann = (1 - v ** n) / j
        return L / ann

We now know the value of the monthly payment which further splits into principal and interest.
The principal is the value that is deducted from the balance. Interest is the part that is the bank's earnings.

Let's start with the interest. The interest is the outstanding balance multiplied by the monthly interest rate.
We haven't yet defined the model variable for balance but we will shortly.

..  code-block:: python
    :caption: model.py

    @variable()
    def interest(t):
        if t == 0:
            return 0
        return balance(t-1) * monthly_interest_rate()

The principal is whatever is left from the monthly payment after deducting interest.

..  code-block:: python
    :caption: model.py

    @variable()
    def principal(t):
        if t == 0:
            return 0
        return payment() - interest(t)

At the start, the value of the balance amounts to the value of the loan.
Afterwards, it decreases by the value of the principal.

..  code-block:: python
    :caption: model.py

    @variable()
    def balance(t):
        if t == 0:
            return main.get("loan")
        else:
            return balance(t-1) - principal(t)

We now have all components of the amortization schedule, so let's take a look at the results.

|

Results
^^^^^^^

Let's take a look at the subset of the results - the first and last year of the loan repayment.

..  code-block:: python

      t  monthly_interest_rate  payment   balance  interest  principal
      0               0.008333   877.57 100000.00      0.00       0.00
      1               0.008333   877.57  99955.76    833.33      44.24
      2               0.008333   877.57  99911.15    832.96      44.61
      3               0.008333   877.57  99866.18    832.59      44.98
      4               0.008333   877.57  99820.82    832.22      45.35
      5               0.008333   877.57  99775.09    831.84      45.73
      6               0.008333   877.57  99728.98    831.46      46.11
      7               0.008333   877.57  99682.48    831.07      46.50
      8               0.008333   877.57  99635.60    830.69      46.88
      9               0.008333   877.57  99588.32    830.30      47.27
     10               0.008333   877.57  99540.65    829.90      47.67
     11               0.008333   877.57  99492.59    829.51      48.07
     12               0.008333   877.57  99444.12    829.10      48.47

     ...

    348               0.008333   877.57   9981.95     89.75     787.82
    349               0.008333   877.57   9187.56     83.18     794.39
    350               0.008333   877.57   8386.55     76.56     801.01
    351               0.008333   877.57   7578.86     69.89     807.68
    352               0.008333   877.57   6764.45     63.16     814.41
    353               0.008333   877.57   5943.25     56.37     821.20
    354               0.008333   877.57   5115.20     49.53     828.04
    355               0.008333   877.57   4280.26     42.63     834.94
    356               0.008333   877.57   3438.36     35.67     841.90
    357               0.008333   877.57   2589.44     28.65     848.92
    358               0.008333   877.57   1733.45     21.58     855.99
    359               0.008333   877.57    870.32     14.45     863.13
    360               0.008333   877.57     -0.00      7.25     870.32

The loan starts with a balance of €100 000. Each month we pay the same amount of €877.57.
At the beginning of the term, the interest is very high and the principal is low. In the end, it's the other way around.
The balance is exactly zero after 360 months.
