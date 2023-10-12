Output
======

The cash flow model generates three types of output files: output, diagnostic, and log.
These files are organized within the :code:`output` folder, as shown below:

..  code-block::

    .
    └── output/
        └── <timestamp>_diagnostic.csv
        └── <timestamp>_log.txt
        └── <timestamp>_output.csv

The numerical results of the model variables are stored in the :code:`<timestamp>_output.csv` file. Users can review
and manipulate the results from this file or utilize the :code:`output` dataframe returned by the :code:`run.py` script.

|

Structure
---------

The output of a cash flow model is presented as a table, where rows represent time periods,
and columns represent model variables. The structure of the output depends on the following settings:

* :code:`AGGREGATE` - this flag determines whether the results should be aggregated or not.
* :code:`T_MAX_OUTPUT` - specifies the number of projection periods included in the output.
* :code:`OUTPUT_COLUMNS` - a list of output columns to be included (by default, all columns are included).

Let's explore these settings with examples.

|

Aggregated output
^^^^^^^^^^^^^^^^^

You can create aggregated output by setting the :code:`AGGREGATE` option to :code:`True`, which is the default setting.

.. code-block:: python
   :caption: setting.py

   settings = {
       ...
       "AGGREGATE": True,
       ...
   }

.. image:: https://acturtle.com/static/img/39/output_aggregated.png
   :align: center

In the aggregated output, results are summed across all model points, resulting in a single set of projections.
The number of rows in this output is determined by :code:`T_MAX_OUTPUT + 1`, where the :code:`+1` accounts for the projection starting at time period 0.

You can also aggregate data by groups. To do this, set the :code:`AGGREGATE` option to :code:`True` and specify
the :code:`GROUP_BY_COLUMN` as the column name containing the grouping variable from your 'main' model point set.

For example, to group results by :code:`product_code`, configure your settings as follows:

.. code-block:: python
   :caption: settings.py

   settings = {
       ...
       "AGGREGATE": True,
       "GROUP_BY_COLUMN": "product_code",
       ...
   }

|

Individual output
^^^^^^^^^^^^^^^^^

To generate individual output, set the :code:`AGGREGATE` option to :code:`False`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "AGGREGATE": False,
        ...
    }

.. image:: https://acturtle.com/static/img/39/output_individual.png
   :align: center

In this case, each model point has its own set of results.

|

Subset of columns
^^^^^^^^^^^^^^^^^

If you only require specific variables in the output, you can select them using the :code:`OUTPUT_COLUMNS` setting:

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "OUTPUT_COLUMNS": ["bel"],
        ...
    }


.. image:: https://acturtle.com/static/img/39/output_subset.png
   :align: center


The :code:`OUTPUT_COLUMNS` setting takes a list of variables names to include in the output.
By default, when this setting is an empty list, results for all model variables are generated.

|

Default vs. custom output
-------------------------

|

Default output
^^^^^^^^^^^^^^

By default, the model's results are saved to a CSV file. This file is saved in the :code:`output` folder
within the model's directory. The filename follows the format :code:`<timestamp>_output.csv`, where :code:`<timestamp>`
represents the date and time when the model was executed (e.g., :code:`20231125_173512_output.csv`).

|

Custom output
^^^^^^^^^^^^^

The default output behavior can be customized to suit specific requirements, such as saving results to
different file formats or uploading them to a database. To use custom output, follow these steps:

1. Set the :code:`SAVE_OUTPUT` setting to :code:`False` in your :code:`settings.py` file.
This prevents the model from saving the output in the default manner:

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        "SAVE_OUTPUT": False,
        ...
    }

2. Modify the :code:`run.py` script to handle custom output.
For instance, you can save results as a text file without timestamps:

..  code-block:: python
    :caption: run.py

    if __name__ == "__main__":
        output = start(settings, sys.argv)
        output.to_string("output.txt")

Now, instead of creating an :code:`<timestamp>_output.csv` file, the script will generate an :code:`output.txt` file
with the results.
