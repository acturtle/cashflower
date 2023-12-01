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

### Configuration

| #  | AGGRE | GROUP | ID | MULTI  | COLS | DIAGN | OUTPU | MAX_CALC | MAX_OUT | VARS | MP  |
|----|-------|-------|----|--------|------|-------|-------|----------|---------|------|-----|
| 01 | True  | None  | id | False  | []   | True  | True  | 720      | 720     | 1    | 1   |
| 02 | True  | None  | id | True   | []   | True  | True  | 720      | 720     | 1    | 1   |
| 03 | True  | None  | id | False  | []   | True  | True  | 720      | 720     | 1    | 100 |
| 04 | True  | None  | id | True   | []   | True  | True  | 720      | 720     | 1    | 100 |
| 05 | False | None  | id | False  | []   | True  | True  | 720      | 720     | 1    | 10  |
| 06 | True  | None  | mp | False  | []   | True  | True  | 720      | 720     | 1    | 10  |
| 07 | True  | None  | id | False  | 1    | True  | True  | 720      | 720     | 8    | 1   |
| 08 | True  | None  | id | False  | []   | False | True  | 720      | 720     | 1    | 1   |
| 09 | True  | None  | id | False  | []   | True  | False | 720      | 720     | 1    | 1   |
| 10 | True  | None  | id | False  | []   | True  | True  | 720      | 720     | 1    | 1   |
| 11 | True  | None  | id | False  | []   | True  | True  | 360      | 360     | 5    | 1   |
| 12 | True  | None  | id | False  | []   | True  | True  | 0        | 0       | 1    | 1   |
| 13 | True  | None  | id | False  | []   | True  | True  | 720      | 720     | 2    | 1   |
| 14 | True  | None  | id | False  | []   | True  | True  | 720      | 720     | 4    | 1   |
| 15 | True  | code  | id | False  | []   | True  | True  | 720      | 720     | 1    | 1   |
| 16 | True  | None  | id | False  | []   | True  | True  | 13       | 13      | 2    | 2   |
| 17 | True  | None  | id | False  | []   | True  | True  | 13       | 13      | 2    | 8   |
| 18 | True  | None  | id | True   | []   | True  | True  | 13       | 13      | 2    | 8   |
| 19 | True  | None  | id | True   | []   | True  | True  | 13       | 13      | 2    | 8   |

### Description

* `01` - basic model created with `create_model()` and default settings
* `02` - basic model with `MULTIPROCESSING = True`
* `03` - basic model with 100 model points
* `04` - basic model with 100 model points and `MULTIPROCESSING = True`
* `05` - basic model with 10 model points and individual results (`AGGREGATE = False`)
* `06` - basic model with 10 model points and id column set to `mp`
* `07` - model with `OUTPUT_COLUMNS = ["f"]`
* `08` - basic model with `SAVE_DIAGNOSTIC = False`
* `09` - basic model with `SAVE_OUTPUT = False`
* `10` - model with variable that is calculated backward
* `11` - model with variables forming a cycle (real estate mortgage)
* `12` - model in which runplan is used
* `13` - model with array variable (`@variable(array=True)`)
* `14` - model that uses `discount()`
* `15` - model with results aggregated by groups (`GROUP_BY_COLUMN = 'product_code'`)
* `16` - model with `variable(aggregation_type="first")`
* `17` - model with `variable(aggregation_type="first")` and `GROUP_BY_COLUMN`
* `18` - model with `variable(aggregation_type="first")` and `MULTIPROCESSING`
* `19` - model with `variable(aggregation_type="first")` and `GROUP_BY_COLUMN` and `MULTIPROCESSING`
* `99` - "special" model for testing memory limits
