
Discount function
=================

Discounting is a common calculation in the actuarial cash flow models.
The :code:`discount()` function available in the package supports the vectorized approach to discounting.

.. code-block:: python

    from cashflower import discount

    @variable(array=True)
    def present_value():
        return discount(cash_flows=cash_flow(), discount_rates=discount_rate())


The :code:`discount()` function takes two mandatory parameters, both of which must be NumPy arrays containing float values:

* :code:`cash_flows` - an array representing the cash flows to be discounted,
* :code:`discount_rates`- an array of forward discount rates corresponding to each period.

The :code:`discount()` function returns an array, so you can specify :code:`@variable(array=True)` for the variable that will hold the result.

|

Scalar equivalent
-----------------

The :code:`discount()` function's calculation is equivalent to the following recursive formula:

.. code-block:: python

    from settings import settings

    @variable()
    def present_value(t):
        if t == settings["T_MAX_CALCULATION"]:
            return cash_flow(t)
        else:
            return cash_flow(t) + present_value(t+1) * cash_flow(t+1)

Using the :code:`discount()` function significantly improves the calculation time.

|

Calculation example
-------------------

Here's an example of how the :code:`discount()` function works:

.. code-block:: python

    import numpy as np
    from cashflower import discount

    cash_flow = np.array([90.00, 120.00, 100.00])
    discount_rate = np.array([1, 0.8, 0.9])
    print(discount(cash_flow, discount_rate))
    # [258. 210. 100.]

In this example, the present values of future cash flows for three periods are calculated as follows:

* :code:`258.0` is the present value of all three cash flows at the beginning of projection :code:`90.0 + 120.0 * 0.8 + 100.0 * 0.8 * 0.9`.
* :code:`210.0` is the present value of two cashflows after the first period :code:`120.0 + 100.0 * 0.9`.
* :code:`100.0` represents the present value of the last cash flow after two periods :code:`100.0`.

Note that the discount rate at time :code:`t` represents the value of :code:`1` at time :code:`t-1`.
