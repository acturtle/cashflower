Run
===

To calculate the model, execute the :code:`run.py` script:

..  code-block::
    :caption: terminal

    python run.py

The model will automatically create an :code:`output` folder if it doesn't already exist.
Inside this folder, the model will generate CSV files containing results and diagnostics,
as well as a text file for the log:

..  code-block::

    .
    └── output/
        └── <timestamp>_diagnostic.csv
        └── <timestamp>_log.txt
        └── <timestamp>_output.csv

|

Run a specific version
^^^^^^^^^^^^^^^^^^^^^^

To run the model with a specific version from the runplan, use the :code:`--version` flag.
For instance, to run version 2, use the following command:

..  code-block::
    :caption: terminal

    python run.py --version 2

This command will execute the model using data for the 2nd version specified in the runplan.

Here's an example of a runplan in the model:

..  code-block::
    :caption: input.py

    runplan = Runplan(data=pd.DataFrame({
        "version": [1, 2, 3],
        "shock": [0, 0.01, -0.01],
    }))

To retrieve values from the runplan within the model's variables, you can use the :code:`get` method
of the :code:`Runplan` class:

..  code-block::
    :caption: model.py

    @variable()
    def shocked_mortality_rate(t):
        return mortality_rate(t) * runplan.get("shock")

If you run the model with version 2, the shock value will be set to :code:`0.01`.

This approach allows you to easily specify and manage different versions of your model using the runplan
and select a particular version when running the model.


Run a specific model point
^^^^^^^^^^^^^^^^^^^^^^^^^^

For analytical or debugging purposes, it is often useful to run the model for a specific model point.

This can be achieved by utilizing the `--id` flag in your command.

For example, to run the model for the model point with id :code:`A123`, execute the following command:

..  code-block::
    :caption: terminal

    python run.py --id "A123"

Executing this command will initiate the model exclusively for the specified model point with ID :code:`A123`.
