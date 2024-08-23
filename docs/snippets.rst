Code snippets
=============

Run all versions from the runplan:

.. code-block:: python

  import os
  from input import runplan
  
  for v in runplan.data["version"]:
      os.system(f"python run.py --version {v}")
