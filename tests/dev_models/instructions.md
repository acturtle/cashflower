## Development models for testing

This directory contains a collection of development models designed for testing new features 
within the package. These models are configured differently to cover various edge cases.

### Usage instructions

1. **Pre-development:** Before implementing a new feature, 
run all the models (`01_initial_runs.py`).

2. **Post-development:** After making changes or implementing a new feature, 
run all the models again and verify that the results remain consistent 
(`02_perform_checks.py`).
   
### Note

The CSV files generated in the output folder are ignored by Git, 
ensuring that they do not clutter the version control system.

## Development models

* `01` - model created with `create_model()`
* `02` - `MULTIPROCESSING = True`
* `03` - 100 model points
* `04` - 100 model points + `MULTIPROCESSING = True`
* `05` - 10 model points + individual results (`GROUP_BY = "id"`)
* `06` - 10 model points + `ID_COLUMN = "mp"`
* `07` - `OUTPUT_VARIABLES = ["f"]`
* `08` - `SAVE_DIAGNOSTIC = True`
* `09` - `SAVE_OUTPUT = True`
* `10` - variable that is calculated backward (`discounted_premium(t+1)`)
* `11` - variables forming a cycle (real estate mortgage)
* `12` - runplan (`python run.py --version 2`)
* `13` - array variable (`@variable(array=True)`)
* `14` - cython function `discount()`
* `15` - results aggregated by groups (`GROUP_BY = 'product_code'`)
* `16` - `variable(aggregation_type="first")`
* `17` - `variable(aggregation_type="first")` + `GROUP_BY`
* `18` - `variable(aggregation_type="first")` + `MULTIPROCESSING`
* `19` - `variable(aggregation_type="first")` + `GROUP_BY` + `MULTIPROCESSING`
* `20` - stochastic variables
* `21` - stochastic variables that form a cycle
* `22` - strongly connected components ("interconnected" cycles)
* `23` - dependent variables and subset in the output (`OUTPUT_VARIABLES`)
* `24` - `"OUTPUT_VARIABLES": ["one", "two", "three"]`
* `25` - two model point sets
* `26` - a chunk (`python run.py --chunk 2 3`)
* `99` - "special" model for testing memory limits
