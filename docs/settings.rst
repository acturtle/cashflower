Settings
========

The settings of the model are defined in the :code:`settings.py` script.

The table below summarizes all available settings.

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Setting
     - Possible values
     - Description
   * - AGGREGATE
     - True / False
     - Flag if results should be aggregated for policyholders.
   * - OUTPUT_COLUMNS
     - empty list of list of strings
     - List of variables to be included in the output. If empty, all variables are included.
   * - POLICY_ID_COLUMN
     - a string
     - The name of the column which contains id of the policy.
   * - SAVE_RUNTIME
     - True / False
     - Flag if an additional file should be created which contains runtime of variables.
   * - T_CALCULATION_MAX
     - integer
     - The maximal month for calculation.
   * - T_OUTPUT_MAX
     - integer
     - The maximal month for output files.


Aggregate
---------

The :code:`AGGREGATE` setting is a flag if the results should be aggregated for policyholders.

If the setting is set to :code:`False`, the results will be on individual level:

..  code-block::
    :caption: <timestamp>_fund.csv

    t,r,fund_value
    0,1,15000.0
    1,1,15030.0
    2,1,15060.06
    3,1,15090.18
    0,1,3000.0
    1,1,3006.0
    2,1,3012.01
    3,1,3018.03
    0,2,9000.0
    1,2,9018.0
    2,2,9036.04
    3,2,9054.11

There are results for 2 policies and 1 of them has two records (record is in column :code:`r`).

If the AGGREGATE setting is set to :code:`True`, the results will aggregated:

..  code-block::
    :caption: <timestamp>_fund.csv

    t,fund_value
    0,27000.0
    1,27054.0
    2,27108.11
    3,27162.32

There is only one set of results which is the sum of all results.

Aggregated results make sense for some but not for all variables.
You can choose the relevant output columns in the :code:`OUTPUT_COLUMNS` setting.

.. WARNING::
   Aggregated results for some variables may not make sense.

|

Output columns
--------------

By default, the model outputs all variables.
If you do not need all of them, provide the list of variables that should be in the output.

The default value of the :code:`OUTPUT_COLUMNS` setting is the empty list (:code:`[]`).
All variables are saved in the output.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "OUTPUT_COLUMNS": [],
        ...
    }

If the model has 3 variables, all of them will be in the output.

..  code-block:: python
    :caption: model.py

    from cashflower import assign, ModelVariable

    a = ModelVariable()
    b = ModelVariable()
    c = ModelVariable()

    @assign(a)
    def a_formula(t):
        return 1*t

    @assign(b)
    def b_formula(t):
        return 2*t

    @assign(c)
    def c_formula(t):
        return 3*t

The result contains all columns.

..  code-block::
    :caption: <timestamp>_policy.csv

    t,r,a,b,c
    0,1,0,0,0
    1,1,1,2,3
    2,1,2,4,6
    3,1,3,6,9
    0,1,0,0,0
    1,1,1,2,3
    2,1,2,4,6
    3,1,3,6,9

The user can choose a subset of columns.


..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "OUTPUT_COLUMNS": ["a", "c"],
        ...
    }

Only the chosen columns are in the output.

..  code-block::
    :caption: <timestamp>_policy.csv

    t,r,a,c
    0,1,0,0
    1,1,1,3
    2,1,2,6
    3,1,3,9
    0,1,0,0
    1,1,1,3
    2,1,2,6
    3,1,3,9

|

Policy ID column
----------------

Each model point must have a column with a key column used for identification of policyholders.
This column is also used to connect records in case of multiple model point.

By default, the column must be named :code:`policy_id`.
The value can be changed using the :code:`POLICY_ID_COLUMN` setting.

The default value for the :code:`POLICY_ID_COLUMN` setting is :code:`policy_id`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "POLICY_ID_COLUMN": "policy_id",
        ...
    }

The model point must have have a column with this name.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPoint

    policy = ModelPoint(data=pd.DataFrame({"policy_id": [1, 2]}))

.. WARNING::
   Column names are case-sensitive. :code:`policy_id` is not :code:`POLICY_ID`.


