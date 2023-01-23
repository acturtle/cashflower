Run
===

To calculate the model, run :code:`run.py`.

..  code-block::
    :caption: terminal

    python run.py

The model will create an :code:`output` folder.
Inside of this folder, the model will create results for each of the model points.

..  code-block::

    .
    └── output/
        ├── <timestamp>_policy.csv
        ├── <timestamp>_fund.csv
        └── <timestamp>_coverage.csv

To run the model with specific version, add the version number at the end of the command.

..  code-block::
    :caption: terminal

    python run.py 2
