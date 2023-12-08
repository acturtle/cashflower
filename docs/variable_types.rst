Variable types
==============

Cashflower includes various types of variables. Here's an overview:

.. list-table::
   :align: left
   :header-rows: 1
   :widths: auto

   * - #
     - Type
     - Definition
     - Calling

   * - 1
     - Regular
     - .. code-block:: python

        @variable()
        def regular_var(t):
            return t

     - .. code-block:: python

        print(regular_var(t=5))
        # 5.0

        print(regular_var())
        # np.array([0., 1., 2., ..., 720.])

   * - 2
     - Constant
     - .. code-block:: python

        @variable()
        def constant_var():
            return 1

     - .. code-block:: python

        print(constant_var(t=5))
        # 1.0

        print(constant_var())
        # 1.0

   * - 3
     - Array
     - .. code-block:: python

        @variable(array=True)
        def array_var():
            return [*range(720)]

     - .. code-block:: python

        print(array_var(t=5))
        # 5.0

        print(array_var())
        # np.array([0., 1., 2., ..., 720.])

   * - 4
     - Stochastic
     - .. code-block:: python

        @variable()
        def stoch_var(t, stoch):
            return interest_rates[t, stoch]

     - .. code-block:: python

        print(stoch_var(t=5, stoch=2))
        # 0.02

Description:

1. Regular

* This is the default variable type with values that depend on :code:`t` (time).
* The function requires a parameter :code:`t` and should return a numeric value.
* You can call it for a specific period (e.g., :code:`t=5`) to get a single float.
  When called without any parameters, it returns an entire array of results, useful for array-based calculations.
* It belongs to the :code:`Variable` class.

|

2. Constant

* Constant variable holds the same value for all periods.
* The function doesn't require any parameters and should return a numeric value.
* It can be called for a specific period (e.g., :code:`t=5`) or without any arguments, returning a float in both cases.
  It can still be used for array-based calculations thanks to broadcasting mechanisms.
* It belongs to the :code:`ConstantVariable` class.

|

3. Array

* Array variables significantly enhance runtime performance compared to regular ones.
* The variable's decorator should include an :code:`array` argument set to :code:`True` (:code:`@variable(array=True)`).
  The function doesn't require any parameters and should return an array of numeric values, matching the projection horizon's length.
* Similar to regular variables, it can be called for a specific period (e.g., :code:`t=5`) to return a single float.
  When called without parameters, it provides the entire array of results for array-based calculations.
* It belongs to the :code:`ArrayVariable` class.

|

4. Stochastic

* Stochastic variables are for models involving multiple stochastic runs.
* The function requires two parameters: :code:`t` and :code:`stoch`, returning a numeric value.
* It can be called for a specific period and stochastic scenario (e.g., :code:`t=5` and :code:`stoch=2`) to return a single float.
* It belongs to the :code:`StochasticVariable` class.
