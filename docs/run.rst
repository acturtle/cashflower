Run
===

To calculate the model, run :code:`run.py`.

..  code-block::
    :caption: terminal

    python run.py

The model will create an :code:`output` folder, if it doesn't exist yet.
Inside of this folder, the model will create a csv file with results and a diagnostic file.

..  code-block::

    .
    └── output/
        └── <timestamp>_output.csv
        └── <timestamp>_diagnostic.csv

To run the model with specific version from the runplan, add the version number at the end of the command.

..  code-block::
    :caption: terminal

    python run.py 2

Now, you can use the data from your runplan. For example:

..  code-block::
    :caption: input.py

    runplan = Runplan(data=pd.DataFrame({
        "version": [1, 2, 3],
        "shock": [0, 0.01, -0.01],
    }))

To read from the runplan, use:

..  code-block::

    runplan.get("shock")

For example:

..  code-block::
    :caption: model.py

    @variable()
    def shocked_mortality_rate(t):
        return mortality_rate(t) * runlan.get("shock")

If you run with version 2, the shock value will amount to :code:`0.01`.
