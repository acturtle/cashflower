How-to's
========

**How to run all versions?**

Run all versions from the runplan:

.. code-block:: python

  import os
  from input import runplan
  
  for v in runplan.data["version"]:
      os.system(f"python run.py --version {v}")


|

**How to pretty-print the output data frame?**

Print all rows and columns of the :code:`output` data frame with 2 decimal places:

..  code-block:: python
    :caption: run.py

    import os
    import pandas as pd
    from cashflower import run
    from settings import settings

    pd.options.display.float_format = '{:.2f}'.format
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 1000)

    if __name__ == "__main__":
        output, diagnostic, log = run(settings=settings, path=os.path.dirname(__file__))
        print(output.to_string(index=False))

|

**How to loop through all records of a model point?**

Let's assume that your model point set is named :code:`fund`.
To iterate over all records of a model point, use :code:`fund.model_point_data.shape[0]` as the upper bound:

..  code-block:: python
    :caption: model.py

    @variable()
    def total_fund():
        total = 0
        for i in range(fund.model_point_data.shape[0]):
            total += fund.get("fund_value", i)
        return total

This code loops through each record and sums the :code:`fund_value` for all records of the model point.

|

**How to run the model from the CLI with custom arguments?**

If you run the model from the command line and want to pass a custom argument, such as a filename for the output,
you can do it as follows:

..  code-block:: bash
    :caption: terminal

    python run.py --filename "my-awesome-output.csv"

You can then retrieve the argument using the :code:`parse_arguments()` function.

Example:

..  code-block:: python
    :caption: run.py

    import os
    from cashflower import run, parse_arguments
    from settings import settings


    if __name__ == "__main__":
        output, diagnostic, log = run(settings=settings, path=os.path.dirname(__file__))
        args, unknown = parse_arguments()
        filename = unknown[1]
        output.to_csv(f"{filename}")
