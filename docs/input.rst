Input
=====

Input for the cash flow model is defined in the :code:`input.py` script.

There are three types of the model's inputs:

* model point sets,
* runplan,
* other assumptions.

|

Model point sets
----------------

Model point sets contain model points. Model points represent objects for which the model is calculated.
The model point can be, for example, a policyholder or a financial instrument.

.. image:: https://acturtle.com/static/img/docs/model_point_sets.png
   :align: center

|

We can define:

* **model point set** - a group of model points; data can be read from a file or a database query result,
* **model point** - one or multiple records that contain data on the given object (e.g. policyholder or financial asset),
* **record** - a single row of data.

|

The model point set is defined using the :code:`ModelPointSet` class.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPointSet

    my_model_point_set = ModelPointSet(data=pd.DataFrame({
        "age": [27, 65, 38],
        "sex": ["F", "M", "M"]
    }))


The cash flow model will calculate results for each of the model points in the model point set.

|

Create a model point set from a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data for the model point set might be stored in a csv file.

..  code-block:: text
    :caption: data-policy.csv

    id,age,sex,premium
    X149,45,F,100
    A192,57,M,130
    D32,18,F,50


To create a model point set, use :code:`ModelPointSet` class and pass a data frame in the :code:`data` parameter.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPointSet

    policy = ModelPointSet(data=pd.read_csv("data-policy.csv"))


A model can have multiple model point sets.

|

Multiple model point sets
^^^^^^^^^^^^^^^^^^^^^^^^^

The model can include  multiple model point sets.

In this case, you need to specify which model point sets are secondary by setting :code:`main` to :code:`False`.
Exactly one model point set should have :code:`main` set to :code:`True`.
The model will loop over the model points of this primary model point set.

Additionally, if multiple model point sets are used, you must set the :code:`id_column` parameter.
This parameter specifies the column in the data used to link records between the model point sets.

For example, the policyholder may hold multiple funds, and each fund has its own record.

Policy data:

..  code-block:: text
    :caption: policy_data

    id     age    sex   premium
    X149   45     F     100
    A192   57     M     130
    D32    18     F     50

Fund data:

..  code-block:: text
    :caption: fund_data

    id     fund_code   fund_value
    X149   10          15000
    A192   10          3000
    A192   12          9000
    D32    8           12500
    D32    14          12500

Policyholder X149 has one fund and policyholders A192 and D32 have two funds each.
The :code:`id` column allows for linking the corresponding records.

Data on these funds is stored in the :code:`fund` model point set.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPointSet

    policy = ModelPointSet(
        data=policy_data,
        id_column="id"
    )

    fund = ModelPointSet(
        data=fund_data,
        main="False",
        id_column="id"
    )

Model point sets are linked by the :code:`id` column.

|

Get value from a model point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To read a value from a model point, use the :code:`get()` method of the :code:`ModelPointSet` class.

..  code-block:: python

        policy.get("age")

|

The model will read the value of the model point which is currently calculated.

..  code-block:: python
    :caption: model.py

    from cashflower import variable
    from input import assumption, policy


    @variable()
    def mortality_rate():
        age = policy.get("age")
        sex = policy.get("sex")
        return assumption["mortality"].loc[age, sex]["rate"]

|

Get multiple records
^^^^^^^^^^^^^^^^^^^^

If a model point contains multiple records, you can access a specific one using the :code:`record_num` parameter.
For example:

..  code-block:: python

    fund.get("fund_value", record_num=1)

Here, :code:`record_num=1` specifies that you are retrieving the value of :code:`fund_value` from the second record
(since Python uses zero-based indexing, :code:`record_num=0` would refer to the first record).

|

If model points have varying number of records, you can use :code:`fund.model_point_data.shape[0]` to determine
the number of records of the model point.

For example, to calculate the total value of fund value, use:

..  code-block:: python

    @variable()
    def total_fund_value():
        total_value = 0
        for i in range(0, fund.model_point_data.shape[0]):
            total_value += fund.get("fund_value", i)
        return total_value

|

Runplan
-------

Runplan is a list of runs that the model should perform.

..  code-block:: python
    :caption: input.py

    import pandas as pd
    from cashflower import Runplan, ModelPointSet

    runplan = Runplan(data=pd.DataFrame({
        "version": [1, 2, 3],
        "shock": [0, 0.05, -0.05]
    }))

You can use different run versions, to calculate different scenarios.

To get data from runplan, use:

..  code-block:: python

    runplan.get("my-column")

For example:

..  code-block:: python
    :caption: model.py

    from input import main, runplan


    @variable()
    def mortality_rate(t):
        ...

    @variable()
    def shocked_mortality_rate(t):
        return mortality_rate(t) * (1 + runplan.get("shock"))

To run the model with the chosen version, source the :code:`run.py` and add the version number.

For example, to run the model with the version :code:`2` , use:

..  code-block:: bash
    :caption: terminal

    python run.py --version 2

The model will take data from runplan for the version 2.

|

Assumptions
-----------

Assumptions contain data that are further used in the model.
The recommended place to store assumptions is the :code:`assumption` dictionary.

For example:

..  code-block:: python
    :caption: input.py

    import pandas as pd
    from cashflower import CSVReader

    assumption = {
        "mortality": CSVReader("input/mortality.csv"),
        "interest_rates": pd.read_csv("input/interest_rates.csv", index_col="T"),
        "expense_acq": 300,
        "expense_maint": 60,
    }

Assumptions for life insurance can include:

* underwriting - mortality, lapses, expenses,
* market - interest rates, inflation,
* product's characteristics.

Assumptions may be e.g. single numerical values, strings or may be stored in a tabular form.

..  code-block:: text
    :caption: mortality.csv

    AGE,MALE,FEMALE
    0,0.003890,0.003150
    1,0.000280,0.000190
    2,0.000190,0.000140
    3,0.000150,0.000110
    4,0.000120,0.000090
    5,0.000100,0.000080
    [...]

..  code-block:: text
    :caption: interest_rates.csv

    T,VALUE
    1,0.00736
    2,0.01266
    3,0.01449
    4,0.01610
    5,0.01687
    [...]

|

CSV Reader
^^^^^^^^^^

In the actuarial models, it is common to use assumptions only to read in a single value from a csv file.
For this purpose, you can use a :code:`CSVReader` class.
It is a simpler construct than, e.g. :code:`pandas` dataframe, but it is faster.

If you want to use :code:`CSVReader`, your data must have row labels in the leftmost columns.
The class always returns strings, so it's up to the user to perform necessary conversions.

To create an instance of :code:`CSVReader` provide the path to the file.

..  code-block:: python

    reader1 = CSVReader("data1.csv")

If your data uses multiple columns for row labels, specify the number of row label columns.

..  code-block::

    reader2 = CSVReader("data2.csv", num_row_label_cols=2)

To get value from the file, use the :code:`get_value` method.

For example:

..  code-block:: text
    :caption: data1.csv

    RowX,Col1,Col2,Col3
    Row1,1.1,2.2,3.3
    Row2,4.4,5.5,6.6
    Row3,7.7,8.8,9.9

..  code-block:: python

    value = float(reader1.get_value("Row2", "Col3"))
    # value is 6.6

If your data has multiple row label columns, provide the tuple of row labels.

..  code-block:: text
    :caption: data2.csv

    X,Y,1,2,3
    1,1,4,5,7
    1,2,9,2,4
    2,1,3,5,2
    2,2,3,9,6

..  code-block:: python

    value = int(reader2.get_value(("2", "1"), "2"))
    # value is 5

|

