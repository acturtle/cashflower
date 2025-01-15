Stochastic variables
====================

Stochastic variables are variables that take two parameters: :code:`t` and :code:`stoch`.

For example:

.. code-block:: python

    @variable()
    def pv_premiums(t, stoch):
        if t == settings["T_MAX_CALCULATION"]:
            return premium(t)
        else:
            return premium(t) + pv_premiums(t+1, stoch) * discount_rate(t+1, stoch)

Stochastic variables are part of stochastic models with multiple plausible future scenarios.
Stochastic models require setting the number of stochastic scenarios within the settings.

.. code-block:: python

    settings = {
        "NUM_STOCHASTIC_SCENARIOS": 5,
    }

This setup initiates computations for the stochastic variable five times.
Each iteration involves variations in the :code:`stoch` parameter, ranging from 1 to 5.
The output presents the averaged results derived from these scenarios.


Procedure
---------

Let's go over the mechanism behind stochastic variables using an example involving the modelling of a fund value.

Consider three equally plausible scenarios for the fund's return:

..  code-block:: python
    :caption: input.py

    import pandas as pd

    scenarios = pd.DataFrame({
        "num": [1, 2, 3],
        "fund_return": [0.10, 0.05, 0.01]
    })
    scenarios.set_index("num", inplace=True)

    assumption = {
        "scenarios": scenarios,
    }

In these scenarios, the fund's value increases in each period by 10%, 5%, and 1% respectively.

The number of stochastic scenarios is set to 3.

..  code-block:: python
    :caption: settings.py

    settings = {
        "NUM_STOCHASTIC_SCENARIOS": 3,
    }

A stochastic variable :code:`fund_value` is created and has two parameters: :code:`t` and :code:`stoch`.

..  code-block:: python
    :caption: model.py

    @variable()
    def fund_value(t, stoch):
        if t == 0:
            return 1_000
        else:
            fund_return = assumption["scenarios"].loc[stoch, "fund_return"]
            return fund_value(t-1, stoch) * (1 + fund_return)

The fund value amounts to 1000 at the beginning of the projection and then increases by the fund return.

There are 3 scenarios of how the fund value will change.

|

**Scenario 1**

In the first scenario, the fund value increases by 10% each period.
The fund value for the first 5 periods amounts to:

..  code-block:: text

     t  fund_return
     0      1000.00
     1      1100.00
     2      1210.00
     3      1331.00
     4      1464.10
     5      1610.51
   ...          ...

|

**Scenario 2**

In the second scenario, the fund return amounts to 5%.

..  code-block:: text

     t  fund_return
     0      1000.00
     1      1050.00
     2      1102.50
     3      1157.63
     4      1215.51
     5      1276.28
   ...          ...

|

**Scenario 3**

In the third scenario, the value of the fund return is 1%.

..  code-block:: text

     t  fund_return
     0      1000.00
     1      1010.00
     2      1020.10
     3      1030.30
     4      1040.60
     5      1051.01
   ...          ...

|

**Result**

The stochastic variable calculates results across these scenarios, averaging them:

..  code-block:: text

     0      (1000.00 + 1000.00 + 1000.00) / 3
     1      (1100.00 + 1050.00 + 1010.00) / 3
     2      (1210.00 + 1102.50 + 1020.10) / 3
     3      (1331.00 + 1157.63 + 1030.30) / 3
     4      (1464.10 + 1215.51 + 1040.60) / 3
     5      (1610.51 + 1276.28 + 1051.01) / 3
   ...                                    ...

The resulting output is:

..  code-block:: text

     t  fund_value
     0     1000.00
     1     1053.33
     2     1110.87
     3     1172.98
     4     1240.07
     5     1312.60
   ...         ...

These values contribute to the model's output file.
