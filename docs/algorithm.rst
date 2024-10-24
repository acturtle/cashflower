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

Memory management
-----------------

Memory management is an important aspect of cash flow modelling. Efficiently managing memory is essential when dealing
with different model configurations and output sizes. Several factors impact the amount of memory consumed during
the modeling process.

Memory consumption
^^^^^^^^^^^^^^^^^^

Factors affecting memory consumption:

1. **Aggregation**:
The :code:`AGGREGATE` setting determines whether the model returns the sum of all results (aggregated) or concatenated individual results.

2. **Projection period**:
The :code:`T_MAX_OUTPUT` setting specifies how many projection periods should be included in the output. A larger projection period increases memory usage.

3. **Number of variables:**
The :code:`OUTPUT_VARIABLES` setting specifies which variables should be part of the output.

The estimated output memory usage:

* :code:`t * v * 8` bytes - for the aggregated output,
* :code:`t * mp * v * 8` bytes - for the individual output.

where:

* :code:`t` - the number of future periods,
* :code:`v` - the number of variables,
* :code:`mp` - the number of model points.

The number of cells are multiplied by :code:`8` because results store 64-bit floats.


Approach
^^^^^^^^

Approach to memory management depends on whether the results are to be aggregated or individual.

**Aggregated output**

For aggregated output, the final result has :code:`t` rows and :code:`v` columns.
However, during calculations, results for each model point are generated individually.
To optimize memory, results are calculated in batches and aggregated after each batch, freeing up memory.
The batch size is determined based on available RAM.

Example:

.. image:: https://acturtle.com/static/img/docs/batches.png
   :align: center


The results for all 9 model points can't be stored in memory at once. So, we split them into 3 batches.

Steps:

1. Calculate results for the first batch (model points 1 to 3).
2. Aggregate results for the first batch (model point results can be removed from memory).
3. Calculate results for the second batch (model points 4 to 6).
4. Aggregate results of the second batch (model point results can be removed from memory).
5. Combine results from the first and second batches (separate batch results can be removed from memory).
6. Calculate results for the third batch (model points 7 to 9).
7. Aggregate results of the third batch (model point results can be removed from memory).
8. Combine results from the first and second batches with the results of the third batch.

The final results are calculated while limiting memory usage.

**Individual output**

In the case of individual output, where the final result has :code:`t * mp` rows and :code:`v` columns,
the entire output object must fit into RAM. The model checks if the output size is within the total available RAM.
If it is, an empty results object is created to allocate memory, which is then filled with calculation results.

For individual results that exceed RAM capacity, an alternative approach is to calculate batches of model points
iteratively and save the results to a CSV file. In this scenario, the :code:`output` DataFrame will not be returned
in the :code:`run.py` script. If you require this feature, please contact us, and we can help with its implementation.

|
