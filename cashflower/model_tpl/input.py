"""
Input for the cash flow model.

Define your model point sets and the runplan here.

Example:
    ```
    from cashflower import ModelPointSet, Runplan
    import pandas as pd

    # Define a model point set with sample data
    policy = ModelPointSet(data=pd.DataFrame({
        "premium": [100, 500, 200]
    }))

    # Define the runplan with multiple scenarios
    runplan = Runplan(data=pd.DataFrame({
        "version": [1, 2],
        "stress": [0, 0.5]
    }))
    ```
"""
