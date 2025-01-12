Run
===

To calculate the model, execute the :code:`run.py` script:

..  code-block:: bash
    :caption: terminal

    python run.py

|

Run a specific version
^^^^^^^^^^^^^^^^^^^^^^

To run the model with a specific version from the runplan, use the :code:`--version` flag.
For instance, to run version 2, use the following command:

..  code-block:: bash
    :caption: terminal

    python run.py --version 2

This command will execute the model using data for the 2nd version specified in the runplan.

Here's an example of a runplan in the model:

..  code-block:: python
    :caption: input.py

    runplan = Runplan(data=pd.DataFrame({
        "version": [1, 2, 3],
        "shock": [0, 0.01, -0.01],
    }))

To retrieve values from the runplan within the model's variables, you can use the :code:`get` method
of the :code:`Runplan` class:

..  code-block:: python
    :caption: model.py

    from input import runplan

    @variable()
    def shocked_mortality_rate(t):
        return mortality_rate(t) * runplan.get("shock")

If you run the model with version 2, the shock value will be set to :code:`0.01`.

This approach allows you to easily specify and manage different versions of your model using the runplan
and select a particular version when running the model.
