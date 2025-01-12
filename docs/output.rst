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


The model will automatically create an :code:`output` folder if it doesn't already exist.
Inside this folder, the model will generate a CSV file containing the output results.
If specified, the model will also save a diagnostics file, which is also in CSV format, and a log file in text format.

|

Structure
---------

The output of a cash flow model is presented as a table, where rows represent time periods,
and columns represent model variables. The structure of the output depends on the following settings:

* :code:`GROUP_BY` - the column name used to group the results.
* :code:`T_MAX_OUTPUT` - specifies the number of projection periods included in the output.
* :code:`OUTPUT_VARIABLES` - a list of output variables to be included (by default, all variables are included).

Let's explore these settings with examples.

|

Grouped output
^^^^^^^^^^^^^^

By default, the :code:`GROUP_BY` is set to :code:`None` which means that the results are aggregated across
all model points.

.. code-block:: python
   :caption: settings.py

   settings = {
       # ...
       "GROUP_BY": None,
       # ...
   }


In the aggregated output, results are summed across all model points, resulting in a single set of projections.
The number of rows in this output is determined by :code:`T_MAX_OUTPUT + 1`, where the :code:`+1` accounts for the projection starting at time period 0.

You can also aggregate data by groups. To do this, specify the :code:`GROUP_BY` as the column name containing
the grouping variable from your model point set.

For example, to group results by :code:`product_code`, configure your settings as follows:

.. code-block:: python
   :caption: settings.py

   settings = {
       # ...
       "GROUP_BY": "product_code",
       # ...
   }

|

Subset of variables
^^^^^^^^^^^^^^^^^^^

The :code:`OUTPUT_VARIABLES` setting takes a list of variables names to include in the output.
By default, when this setting is an empty list, results for all model variables are generated.

If you only require specific variables in the output, you can select them using the :code:`OUTPUT_VARIABLES` setting:

..  code-block:: python
    :caption: settings.py

    settings = {
        # ...
        "OUTPUT_VARIABLES": ["bel"],
        # ...
    }


..  code-block::
    :caption: output

    t    bel
    0    27000.0
    1    27054.0
    2    27108.11
    3    27162.32
    ...  ...
    720  31413.12

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
        # ...
        "SAVE_OUTPUT": False,
        # ...
    }

2. Modify the :code:`run.py` script to handle custom output.
For instance, you can save results as a text file without timestamps:

..  code-block:: python
    :caption: run.py

    if __name__ == "__main__":
        output = run(settings)
        output.to_string("output.txt")

Now, instead of creating an :code:`<timestamp>_output.csv` file, the script will generate an :code:`output.txt` file
with the results.
