[![PyPI Latest Release](https://img.shields.io/pypi/v/cashflower.svg)](https://pypi.org/project/cashflower/)
[![pytest](https://github.com/acturtle/cashflower/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/acturtle/cashflower/actions/workflows/pytest.yml)
[![Documentation Status](https://readthedocs.org/projects/cashflower/badge/)](https://cashflower.acturtle.com)

# Info

Cashflower is an open-source Python framework for actuarial cash flow models.

# Prerequisites

Python version >=3.9

# Usage

## Installation

*terminal*
```
pip install cashflower
```

## Create model

*python console*
```python
from cashflower import create_model

create_model("my_model")
```

Creates:

```
my_model/
    input.py
    model.py
    run.py
    settings.py
```

## Input

*my_model/input.py*
```python
runplan = Runplan(data=pd.DataFrame({"version": [1]}))

main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
```

## Model

*my_model/model.py*
```python
@variable()
def projection_year(t):
    if t == 0:
        return 0
    elif t % 12 == 1:
        return projection_year(t - 1) + 1
    else:
        return projection_year(t - 1)
```

## Calculate

*terminal*
```
python run.py
```

# Contribution

The cashflower package is open-source. Everyone can use it and contribute to its development.

GitHub repository:

[https://github.com/acturtle/cashflower](https://github.com/acturtle/cashflower)

Documentation:

[https://cashflower.acturtle.com](https://cashflower.acturtle.com)
