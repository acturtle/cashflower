[![PyPI Latest Release](https://img.shields.io/pypi/v/cashflower.svg)](https://pypi.org/project/cashflower/)
[![pytest](https://github.com/acturtle/cashflower/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/acturtle/cashflower/actions/workflows/pytest.yml)
[![Documentation Status](https://readthedocs.org/projects/cashflower/badge/)](https://cashflower.acturtle.com)

# Info

Cashflower is an open-source Python framework for actuarial cash flow models.

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

## Model

*my_model/model.py*
```python
from cashflower import variable

@variable()
def survival_probability(t):
    mortality_rate = 0.01
    if t == 0:
        return 1
    return survival_probability(t - 1) * (1 - mortality_rate)
```

## Calculate

*terminal*
```
python run.py
```

# Contribution

GitHub repository:

[https://github.com/acturtle/cashflower](https://github.com/acturtle/cashflower)

Documentation:

[https://cashflower.acturtle.com](https://cashflower.acturtle.com)
