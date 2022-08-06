# Info

Cashflower is a Python framework for actuarial cash flow models.

# Usage

## Installation

terminal
```
pip install cashflower
```

## Create model

python console
```python
from cashflower.admin import create_model

create_model("wol")
```

## Input

wol/modelpoint.py
```python
policy = ModelPoint(name="policy", data=pd.read_csv("C:/my_data/policy.csv"))
```


wol/assumptions.py
```python
assumption = dict()
assumption["interest_rates"] = pd.read_csv("C:/my_data/interest_rates.csv")
assumption["mortality"] = pd.read_csv("C:/my_data/mortality.csv")
```

## Model

wol/policy.py
```python
age = ModelVariable(modelpoint=policy)
death_prob = ModelVariable(modelpoint=policy)

@assign(age)
def age_formula(t):
    if t == 0:
        return int(policy.get("AGE"))
    elif t % 12 == 0:
        return age(t-1) + 1
    else:
        return age(t-1)


@assign(death_prob)
def death_prob_formula(t):
    sex = policy.get("SEX")
    if age(t) <= 100:
        yearly_rate = float(get_cell(assumption["mortality"], sex, AGE=age(t)))
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

