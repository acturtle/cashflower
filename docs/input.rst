Input
=====

Input for the model is defined in the :code:`input.py` script.

There are three types of the model's inputs:

* model point,
* assumptions,
* runplan.

Model point
-----------

Model point contains policy data such as age, sex and premium.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPoint

    policy = ModelPoint(data=pd.DataFrame({"policy_id": [1, 2, 3]}))


The cash flow model will calculate results for each of the policies in the model point.

|

**Create model point**

The data for the model point might be stored in a csv file.

..  code-block::
    :caption: data-policy.csv

    policy_id,age,sex,premium
    X149,45,F,100
    A192,57,M,130
    D32,18,F,50

The primary model point **must** be called :code:`policy`.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPoint

    policy = ModelPoint(data=pd.read_csv("data-policy.csv"))

To create a model point, use :code:`ModelPoint()` class and pass a data frame in the :code:`data` parameter.

A model can have multiple model points but at least one of them must be assigned to a variable :code:`policy`.
The :code:`policy` model point must have unique keys.

.. IMPORTANT::
   Each model must have a model point assigned to a variable called :code:`policy`.

|

By default, the identifiers of policies are stored in the column :code:`policy_id`.
The column name can be changed in the :code:`settings.py`.

.. IMPORTANT::
   The :code:`policy` model point has one record per policyholder.

|

**Multiple model points**

The model can have multiple model points. The :code:`policy` model point must have one record per policyholder.
The other model points might have multiple records for each policyholder.

For example, the policyholder holds multiple funds. Each fund has its own record.

..  code-block::
    :caption: data-fund.csv

    policy_id,fund_code,fund_value
    X149,10,15000
    A192,10,3000
    A192,12,9000
    D32,8,12500
    D32,14,12500

Policyholder X149 has one fund and policyholders A192 and D32 have two funds.

Data on these funds are stored in the :code:`fund` model point.

..  code-block:: python
    :caption: input.py

    from cashflower import ModelPoint

    policy = ModelPoint(data=pd.read_csv("data-policy.csv"))
    fund = ModelPoint(data=pd.read_csv("data-fund.csv"))

Model points link with each other by the :code:`policy_id` column.


Assumptions
-----------

Assumptions contain data for predicting the future.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    assumption = dict()
    assumption["mortality"] = pd.read_csv("input/mortality.csv", index_col="AGE")
    assumption["interest_rates"] = pd.read_csv("input/interest_rates.csv", index_col="T")


Assumptions include:

* underwriting - mortality, lapses, expenses,
* market - interest rates, inflation,
* product's characteristics.

Assumptions are stored in a tabelaric form.

..  code-block::
    :caption: mortality.csv

    AGE,MALE,FEMALE
    0,0.003890,0.003150
    1,0.000280,0.000190
    2,0.000190,0.000140
    3,0.000150,0.000110
    4,0.000120,0.000090
    5,0.000100,0.000080
    [...]

..  code-block::
    :caption: interest_rates.csv

    T,VALUE
    1,0.00736
    2,0.01266
    3,0.01449
    4,0.01610
    5,0.01687
    [...]

Assumptions are stored as a dictionary. Each item in the dictionary is a data frame.

..  code-block:: python
    :caption: input.py

    import pandas as pd

    assumption = dict()
    assumption["mortality"] = pd.read_csv("mortality.csv", index_col="AGE")
    assumption["interest_rates"] = pd.read_csv("interest_rates.csv", index_col="T")

To add new assumptions, create a new key in the :code:`assumption` dictionary and assing a data frame to it.

Runplan
-------

Runplan is a list of runs which models should perform.

..  code-block:: python
    :caption: input.py

    import pandas as pd
    from cashflower import Runplan, ModelPoint

    runplan = Runplan(data=pd.DataFrame({
        "version": [1, 2, 3],
        "shock": [0, 0.05, -0.05]
    }))