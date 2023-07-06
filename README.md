[![PyPI Latest Release](https://img.shields.io/pypi/v/cashflower.svg)](https://pypi.org/project/cashflower/)
[![pytest](https://github.com/acturtle/cashflower/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/acturtle/cashflower/actions/workflows/pytest.yaml)
[![Documentation Status](https://readthedocs.org/projects/cashflower/badge/)](https://cashflower.acturtle.com)

# Info

Cashflower is an open-source Python framework for actuarial cash flow models.

# Prerequisities

Python version >=3.9

# Usage

## Installation

terminal
```
pip install cashflower
```

## Create model

python console
```python
from cashflower import create_model

create_model("my_model")
```

## Input

my_model/input.py
```python
main = ModelPointSet(data=pd.read_csv("C:/my_data/main.csv"))

assumption = dict()
assumption["interest_rates"] = pd.read_csv("C:/my_data/interest_rates.csv")
assumption["mortality"] = pd.read_csv("C:/my_data/mortality.csv", index_col="age")
```

## Model

my_model/model.py
```python
@variable()
def age(t):
    if t == 0:
        return int(main.get("AGE"))
    elif t % 12 == 0:
        return age(t-1) + 1
    else:
        return age(t-1)


@variable()
def death_prob(t):
    if age(t) == age(t-1):
        return death_prob(t-1) 
    elif age(t) <= 100:
        sex = main.get("SEX")
        yearly_rate = assumption["mortality"].loc[age(t)][sex]
        monthly_rate = (1 - (1 - yearly_rate)**(1/12))
        return monthly_rate
    else:
        return 1
```

## Calculate

Run `run.py`

# Contribution

The cashflower package is open-source. Everyone can use it and contribute to its development.

GitHub repository:

[https://github.com/acturtle/cashflower](https://github.com/acturtle/cashflower)

Documentation:

[https://cashflower.acturtle.com](https://cashflower.acturtle.com)
