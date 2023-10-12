Settings
========

The settings of the model are defined in the :code:`settings.py` script.

The table below summarizes available settings.

.. list-table::
   :widths: 20 20 20 40
   :header-rows: 1

   * - Setting
     - Possible values
     - Default value
     - Description
   * - AGGREGATE
     - :code:`True` / :code:`False`
     - :code:`True`
     - Flag indicating whether results should be aggregated.
   * - GROUP_BY_COLUMN
     - a string
     - :code:`None`
     - The column in the 'main' model point set to group aggregated results.
   * - ID_COLUMN
     - a string
     - :code:`id`
     - The column in the 'main' model point set containing identifiers of the model points.
   * - MULTIPROCESSING
     - :code:`True` / :code:`False`
     - :code:`False`
     - Flag indicating whether multiple CPUs should be used for calculations.
   * - OUTPUT_COLUMNS
     - empty list or list of strings
     - :code:`[]`
     - List of variables to be included in the output. If the list is empty, all variables are included.
   * - SAVE_DIAGNOSTIC
     - :code:`True` / :code:`False`
     - :code:`True`
     - Flag indicating whether a diagnostic file should be created.
   * - SAVE_LOG
     - :code:`True` / :code:`False`
     - :code:`True`
     - Flag indicating whether a log file should be created.
   * - SAVE_OUTPUT
     - :code:`True` / :code:`False`
     - :code:`True`
     - Flag indicating whether output file should be created.
   * - T_MAX_CALCULATION
     - integer
     - :code:`720`
     - The maximal month for calculation.
   * - T_MAX_OUTPUT
     - integer
     - :code:`720`
     - The maximal month for output file.


AGGREGATE
---------

The :code:`AGGREGATE` setting is a flag if the results should be aggregated for model points.

If the setting is set to :code:`False`, the results will be on the individual level:

..  code-block::
    :caption: <timestamp>_output.csv

    t,fund_value
    0,15000.0
    1,15030.0
    2,15060.06
    3,15090.18
    0,3000.0
    1,3006.0
    2,3012.01
    3,3018.03
    0,9000.0
    1,9018.0
    2,9036.04
    3,9054.11

There are results for 3 separate model points.

If the AGGREGATE setting is set to :code:`True`, the results will be aggregated:

..  code-block::
    :caption: <timestamp>_output.csv

    t,fund_value
    0,27000.0
    1,27054.0
    2,27108.11
    3,27162.32

There is only one set of results which is the sum of all results.

|

GROUP_BY_COLUMN
---------------


The :code:`GROUP_BY_COLUMN` setting is used to specify the column for grouping the aggregated results.
By default, this setting is configured as :code:`None`, which means that results are aggregated for all model points without grouping.

When you specify a column from the 'main' model point set that defines groups, the results will be grouped based on the values in this attribute.

For instance, if you want to group the results by the :code:`product_code`, you can set the :code:`GROUP_BY_COLUMN`
in your configuration file, :code:`settings.py`, as follows:

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "GROUP_BY_COLUMN": "product_code",
        ...
    }

|

Ensure that there is a corresponding column in your 'main' model point set, as shown in :code:`input.py`:

..  code-block:: python
    :caption: input.py

    main = ModelPointSet(data=pd.DataFrame({
        "id": [1, 2, 3],
        "product_code": ["A", "B", "A"]
    }))

|

The resulting output will contain aggregated results grouped by the specified column, as demonstrated in the following CSV output:

..  code-block::
    :caption: <timestamp>_output.csv

    t,product_code,fund_value
    0,A,24000
    1,A,24048
    2,A,24096.1
    3,A,24144.29
    0,B,3000
    1,B,3006
    2,B,3012.01
    3,B,3018.03


By setting the :code:`GROUP_BY_COLUMN` appropriately, you can conveniently aggregate and group your results according to your specific needs.

|

ID_COLUMN
---------

Each model point must have a column with a key column used for identification.
This column is also used to connect records in case of multiple model point.

By default, the column must be named :code:`id`.
The value can be changed using the :code:`ID_COLUMN` setting.

.. WARNING::
   Column names are case-sensitive. :code:`id` is something else than :code:`ID`.

|

The default value for the :code:`ID_COLUMN` setting is :code:`id`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "ID_COLUMN": "id",
        ...
    }

The model point must have a column with this name.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPointSet

    main = ModelPointSet(data=pd.DataFrame({"id": [1, 2]}))

|

The key column might have other name.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "ID_COLUMN": "policy_number",
        ...
    }

The model point must have a column with this name.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPointSet

    main = ModelPointSet(data=pd.DataFrame({"policy_number": [1, 2]}))

|

MULTIPROCESSING
---------------

By default, the model is evaluated for each model point one after another in a linear process.
If the computer has multiple cores, it's possible to perform calculations in parallel.

.. image:: https://acturtle.com/static/img/28/multiprocessing.png
   :align: center

If :code:`MULTIPROCESSING` is turned on, the model will split all model points into several parts (as many as the number of cores).
It will calculate them in parallel on separate cores and then merge together into a single output.

Thanks to that, the runtime will be decreased. The more cores, the faster calculation.

It is recommended to use :code:`MULTIPROCESSING`  when the model is stable because the log message are more vague.
For the development phase, it is recommended to use single core.

|

OUTPUT_COLUMNS
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

    from cashflower import variable

    @variable(a)
    def a(t):
        return 1*t

    @variable(b)
    def b(t):
        return 2*t

    @variable(c)
    def c(t):
        return 3*t

The result contains all columns.

..  code-block::
    :caption: <timestamp>_output.csv

    t,a,b,c
    0,0,0,0
    1,1,2,3
    2,2,4,6
    3,3,6,9
    0,0,0,0
    1,1,2,3
    2,2,4,6
    3,3,6,9

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
    :caption: <timestamp>_output.csv

    t,a,c
    0,0,0
    1,1,3
    2,2,6
    3,3,9
    0,0,0
    1,1,3
    2,2,6
    3,3,9

|

SAVE_DIAGNOSTIC
---------------

The :code:`SAVE_DIAGNOSTIC` setting is a boolean flag that determines whether the model should save diagnostic information.

|

By default, the setting is set to :code:`True`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "SAVE_DIAGNOSTIC": True,
        ...
    }

When the :code:`SAVE_DIAGNOSTIC` setting is set to :code:`True`, the model saves a file named :code:`<timestamp>_diagnostic.csv` in the output folder:

..  code-block::

    .
    └── output/
        └── <timestamp>_diagnostic.csv

|

If you set :code:`SAVE_DIAGNOSTIC` to :code:`False`, the diagnostic file will not be created.

The diagnostic file contains various pieces of information about the model's variables, such as:

..  code-block::
    :caption: <timestamp>_diagnostic.csv

    variable,calc_order,cycle,calc_direction,type,runtime
    a,1,False,irrelevant,default,5.4
    c,2,False,backward,constant,2.7
    b,3,False,forward,array,7.1

This file can be valuable for gaining insights into the model's behavior, identifying variables that require the most
processing time, and optimizing them for better performance.

Using the diagnostic file is helpful for understanding and improving the model's performance.

|

SAVE_LOG
--------

The :code:`SAVE_LOG` setting is a boolean flag that controls whether the model should save its log to a file.

By default, the setting is set to :code:`True`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "SAVE_LOG": True,
        ...
    }

When :code:`SAVE_LOG` is set to :code:`True`, the model will save a file named :code:`<timestamp>_log.txt` in the output folder:

..  code-block::

    .
    └── output/
        └── <timestamp>_log.txt

If you change the :code:`SAVE_LOG` setting to :code:`False`, no log file will be created.

|

The log file contains saved log messages that are printed to the console during the model's execution.
It provides a record of key events and settings, which can be valuable for troubleshooting
and tracking the model's behavior.

Here is an example of the content of the log file (:code:`<timestamp>_log.txt`):

..  code-block:: python
    :caption: <timestamp>_log.txt

    09:40:49 | Building model 'example'
    09:40:49 | Timestamp: 20230920_094049
    09:40:49 | Settings:
               AGGREGATE: True
               MULTIPROCESSING: False
               OUTPUT_COLUMNS: []
               ID_COLUMN: id
               SAVE_DIAGNOSTIC: True
               SAVE_LOG: True
               SAVE_OUTPUT: True
               T_MAX_CALCULATION: 720
               T_MAX_OUTPUT: 720
    09:40:49 | Reading model components
    09:40:49 | Total number of model points: 1
    09:40:49 | Preparing output
    09:40:49 | Finished
    09:40:49 | Saving output file:
               output/20230920_094049_output.csv
    09:40:49 | Saving diagnostic file:
               output/20230920_094049_diagnostic.csv
    09:40:49 | Saving log file:
               output/20230920_094049_log.txt


The log file is a valuable resource for understanding the model's execution flow and can be particularly useful for
diagnosing issues or reviewing the model's behavior at a later time.

SAVE_OUTPUT
-----------

The :code:`SAVE_OUTPUT` setting is a boolean flag that determines whether the model should save its results to a file.

By default, the setting is set to :code:`True`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "SAVE_OUTPUT": True,
        ...
    }

When :code:`SAVE_OUTPUT` is set to :code:`True`, the model will save a file named :code:`<timestamp>_output.csv` in the output folder:

..  code-block::

    .
    └── output/
        └── <timestamp>_output.csv

If you change the :code:`SAVE_OUTPUT` setting to :code:`False`, no output file will be created.

|

You can use this setting to customize output file creation or perform other actions with the results, such as saving them to a database.

To create custom output files, you can utilize the :code:`output` variable in the :code:`run.py` script.

..  code-block:: python
    :caption: run.py

    if __name__ == "__main__":
    output = start(settings, sys.argv)
    output.to_csv(f"results/my_awesome_results.csv")

The output variable contains a data frame with the results. In the example above, it will create a CSV file named
:code:`my_awesome_results.csv` in the :code:`results` folder:

..  code-block::

    .
    └── results/
        └── my_awesome_results.csv

You can leverage this feature to tailor the output to your specific needs or further process the results as required.

|

T_MAX_CALCULATION
-----------------

The :code:`T_MAX_CALCULATION` is the maximal month of the calculation.

The model will calculate results for all time periods from :code:`0` to :code:`T_MAX_CALCULATION`.

By default, the setting is set to :code:`720` months (:code:`60` years).

|

T_MAX_OUTPUT
------------

The :code:`T_MAX_OUTPUT` is the maximal month in the output file.

By default, the model will save results for :code:`720` months.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "T_MAX_OUTPUT": 720,
        ...
    }

If the setting gets changed, then the number of rows in the output file will change.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "T_MAX_OUTPUT": 3,
        ...
    }

The file saves only results for the first 3 months.

..  code-block::
    :caption: <timestamp>_output.csv

    t,fund_value
    0,27000.0
    1,27054.0
    2,27108.11
    3,27162.32

:code:`T_MAX_OUTPUT` can't be greater than :code:`T_MAX_CALCULATION`.

.. WARNING::
    Model will set :code:`T_MAX_OUTPUT` to :code:`min(T_MAX_OUTPUT, T_MAX_CALCULATION)`.
