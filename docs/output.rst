Output
======

Structure
---------

The output of a cash flow model is a table where rows are periods and columns are model components.

The structure of the output depends on two settings:

* :code:`AGGREGATE` - the flag if the results should be aggregated or not,
* :code:`OUTPUT_COLUMNS` - list of output columns (by default - all).

The output depends also on whether components are model variables or constants.
Constants are not part of the aggregated output because they may be strings.

Let's see some examples.

|

Individual output
^^^^^^^^^^^^^^^^^

An individual output can be created by setting :code:`AGGREGATE` to :code:`False`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        AGGREGATE = False,
        ...
    }

The example of the individual output:

.. image:: https://acturtle.com/static/img/39/output_individual_2.png
   :align: center

The rows represent the projection periods. The column :code:`t` contains the projection month.
Each record of the model point has its own set of results. The record number is included in the :code:`r` column.

The :code:`main` model point set can not have multiple records so the record is always 1.
Other model point sets may have multiple records. In this example, the second model point in the :code:`fund` model point set has 2 records.

The number of projection periods is settable with :code:`T_MAX_OUTPUT`. The individual output includes both model variables and constants.

|

Aggregated output
^^^^^^^^^^^^^^^^^

The aggregated output can be created by setting :code:`AGGREGATE` to :code:`True`.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        AGGREGATE = True,
        ...
    }

The example of the aggregated output:

.. image:: https://acturtle.com/static/img/39/output_aggregated_2.png
   :align: center

The results of the aggregated output are summed across all model points.

There is only one set of projections, so the number of rows amounts to :code:`T_MAX_OUTPUT+1`.
The value is incremented by 1 because the projection starts at 0.
There is no :code:`r` column because there are no separate results for each record.

Also, the output only contains model variables. There are no constants because constants may be of character type.

|

Subset of columns
^^^^^^^^^^^^^^^^^

If not all model components are needed in the output, a subset of columns can be chosen using the :code:`OUTPUT_COLUMNS` setting.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        OUTPUT_COLUMNS = ["bel"],
        ...
    }

The value of this setting is a list containing the names of the model components in the output.

.. image:: https://acturtle.com/static/img/39/output_subset_2.png
   :align: center

Here, the output contains only the column :code:`bel`.

|

Default vs custom output
------------------------

|

Default output
^^^^^^^^^^^^^^

By default, the results of the model are saved to files with comma-separated values.
Files are saved in the output folder in the same directory as the model.

The filenames have the form: :code:`<timestamp>_<model_point_set_name>.csv` (for example: :code:`20231125_173512_main.csv`).

Timestamp contains the moment when the model has finished its work. Timestamp is of the format :code:`YYYYMMDD_hhmmss`, where:

* :code:`YYYY` - year,
* :code:`MM` - month,
* :code:`DD` - day,
* :code:`hh` - hours,
* :code:`mm` - minutes,
* :code:`ss` - seconds.

The model creates as many files as there are model point sets.
There will be always at least one output file - the one for the main model point set (:code:`<timestamp>_main.csv`).

|

Custom output
^^^^^^^^^^^^^

The default output creation can be changed and adjusted to user's needs - e.g. to save to other files or upload to a database.

To use the custom output, two steps need to be followed.

Firstly, set the :code:`SAVE_OUTPUT` setting to :code:`False`. The model will stop saving the output in the default way.

..  code-block:: python
    :caption: settings.py

    settings = {
        ...
        SAVE_OUTPUT = False,
        ...
    }

Now, the model will not save the :code:`.csv` files on its own.

Secondly, adjust the code in the :code:`run.py` script. In the script, you can find the following piece of code:

..  code-block:: python
    :caption: run.py

    if __name__ == "__main__":
        output = start("example", settings, sys.argv)

The :code:`output` object is a dictionary. Its keys are names of model point sets and values are pandas data frames.

Let's say, we don't want to have timestamps in the filenames and want to save the results as text files.

We can do it by adding the following code:

..  code-block:: python
    :caption: run.py

    for key in output.keys():
        output[key].to_string(f"{key}.txt")

We iterate over the keys of the output which are the names of the model point sets.
The :code:`output[key]` is the data frame which we save to a text file.

Now, instead of :code:`output/<timestamp>_main.csv`, we will create the :code:`main.txt` file.