Algorithm
=========

Calculation order
-----------------

In a cash flow model, variables often depend on other variables, creating a complex web of dependencies.
To prevent recursion errors and ensure accurate calculations, the model follows a specific order when processing these
variables.

1. **Directed Graph**: The model identifies dependencies by creating a directed graph, revealing which variables call other variables.

2. **Initialization**: Variables without any predecessors are calculated first. They are removed from the graph, and the process continues until all such variables are processed.

3. **Handling Cycles**: If there are variables with cyclic dependencies, they are assigned the same calculation order index and computed simultaneously.

This approach guarantees that variables are calculated in an order that respects their dependencies and mitigates the risk of recursion errors.

|

Ordering example
^^^^^^^^^^^^^^^^

**Step 1:** The model consists of 8 variables. Two of these variables, :code:`A` and :code:`B`, do not have any predecessors.
To determine the calculation order, we start with the first variable in alphabetical order, which is :code:`A`.
We assign it a calculation order of :code:`1` and remove it from the calculation graph.

.. image:: https://acturtle.com/static/img/docs/calc_order_01.png
   :align: center

**Step 2:** Now, the only remaining variable without predecessors is :code:`B`.
We assign it a calculation order of :code:`2` and remove it from the graph.

.. image:: https://acturtle.com/static/img/docs/calc_order_02.png
   :align: center

**Step 3**: At this point, there are no more variables without predecessors because there is a cyclic dependency between variables :code:`C`, :code:`D`, and :code:`E`.
To handle cyclic dependencies, we assign the entire cycle the same calculation order, which is :code:`3`, indicating that these variables will be evaluated simultaneously.
Afterward, all three variables are removed from the graph.

.. image:: https://acturtle.com/static/img/docs/calc_order_03.png
   :align: center

**Step 4**: The process continues until all variables have been assigned a calculation order.
The next variables to be processed are :code:`F` with an order of :code:`4`, :code:`G` with an order of :code:`5`, and :code:`H` with an order of :code:`6`.

.. image:: https://acturtle.com/static/img/docs/calc_order_04.png
   :align: center

|

Output subset
^^^^^^^^^^^^^

Users have the flexibility to choose a specific subset of output variables through the :code:`OUTPUT_VARIABLES` setting.

For instance, let's consider a scenario where the user has configured their settings to output only the variable :code:`F`:

..  code-block:: python
    :caption: settings.py

    settings = {
        "OUTPUT_VARIABLES": ["F"],
    }

In this case, variables :code:`G` and :code:`H` are not required for the desired output and can be safely omitted from the calculation graph and the model itself.

.. image:: https://acturtle.com/static/img/docs/calc_order_05.png
   :align: center

The model only needs to evaluate variable :code:`F` and its predecessors.

|
