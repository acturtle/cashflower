Array variables
===============

Array variables can be defined by decorating a function with the :code:`@variable` decorator, with the :code:`array` parameter set to :code:`True`.

For example:

.. code-block:: python

    @variable(array=True)
    def pv_net_cf():
        return pv_premiums() - pv_claims() - pv_expenses()

Array variables significantly optimize calculation runtimes by leveraging the :code:`NumPy` package
and its broadcasting mechanism. Instead of performing calculations for each period separately, array variables compute
results in a single operation for the entire variable.

**When to use**

Array variables offer improved runtime performance compared to regular variables but come with increased complexity
in their construction. The decision of whether to use array variables ultimately rests with the actuarial modeller.
If your model has a limited number of model points, and runtime is satisfactory, it may be best to stick with regular
variables for readability.

On the other hand, if runtime is critical, array variables can be beneficial. It's advisable to start arrayizing
variables with simple logic, such as those that involve only addition or multiplication of other variables or scalars.

|

Construction
------------

Consider this array variable example:

.. code-block:: python

    from settings import settings

    @variable(array=True)
    def array_var():
        return [x for x in range(settings["T_MAX_CALCULATION"]+1)]

Breaking down each line:

.. code-block:: python

    @variable(array=True)

Array variables use the :code:`@variable` decorator, but they require setting the :code:`array` parameter to :code:`True`.

.. code-block:: python

    def array_var():

The function does not take the :code:`t` parameter; it remains empty.

.. code-block:: python

    return [x for x in range(settings["T_MAX_CALCULATION"]+1)]

The array variable should return a numeric iterable of a size equal to the :code:`T_MAX_CALCULATION+1` setting
(by default 721). This iterable will be internally converted to a NumPy array of type float64.

|

**Defining array variable using results of regular variables**

You can create array variables using results of regular variables:

.. code-block:: python

    @variable(array=True)
    def pv_net_cf():
        return pv_premiums() - pv_claims() - pv_expenses()


For example, :code:`pv_premiums` is a regular t-dependent variable.

.. code-block:: python

    @variable()
    def pv_premiums(t):
        if t == settings["T_MAX_CALCULATION"]:
            return premiums(t) * discount(t)
        return premiums(t) * discount(t) + pv_premiums(t+1)

Calling :code:`pv_premiums` with a specific :code:`t` value returns the result for that period:

.. code-block:: python

    print(pv_premiums(t=10))
    # 126.12

But calling :code:`pv_premiums` without any argument will return the NumPy array of results:

.. code-block:: python

    print(pv_premium())
    # np.array([145.45, 142.37, ..., 9.35])

The results are based on :code:`NumPy` arrays, so they utilize the broadcasting mechanism.
That's why they can be used in the creation of :code:`pv_net_cf` with simple subtraction and addition operations.

|

Cycle limitations
-----------------

Variables cannot be arrayized if they are part of a cycle. A cycle refers to a group of variables that depend on
each other cyclically. For example:

.. code-block:: python

    @variable()
    def a(t):
        return 2 * b(t)


    @variable()
    def b(t):
        if t == 0:
            return 0
        return c(t-1)


    @variable()
    def c(t):
        return a(t) + 2

In this case, variable :code:`a` relies on :code:`b`, :code:`b` relies on :code:`c`, and :code:`c` in turn relies on :code:`a`.

For example, trying to set up the variable :code:`a` as an array variable like this won't work:

.. code-block:: python

    @variable(array=True)
    def a():
        return 2 * b()

This causes an error because cyclical variables are calculated simultaneously for each :code:`t` separately.
The full results of :code:`b` are not known before calculating :code:`a`.

You can identify variables that are part of a cycle by inspecting the diagnostic file.

|
