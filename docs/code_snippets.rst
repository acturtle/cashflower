Code snippets
=============

**How to run all versions?**

Run all versions from the runplan:

.. code-block:: python

  import os
  from input import runplan
  
  for v in runplan.data["version"]:
      os.system(f"python run.py --version {v}")



|

**How to pretty-print a data frame?**

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
        output = run(settings=settings, path=os.path.dirname(__file__))
        print(output)

