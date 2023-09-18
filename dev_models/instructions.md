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

| #  | AGGRE | ID | MULTI | COLS | DIAGN | OUTPU | MAX_CALC | MAX_OUT | VARS | MP  |
|----|-------|----|-------|------|-------|-------|----------|---------|------|-----|
| 01 | True  | id | False | []   | True  | True  | 720      | 720     | 1    | 1   |
| 02 | True  | id | True  | []   | True  | True  | 720      | 720     | 1    | 1   |
| 03 | True  | id | False | []   | True  | True  | 720      | 720     | 1    | 100 |
| 04 | True  | id | True  | []   | True  | True  | 720      | 720     | 1    | 100 |
| 05 | False | id | False | []   | True  | True  | 720      | 720     | 1    | 10  |
| 06 | True  | mp | False | []   | True  | True  | 720      | 720     | 1    | 10  |
| 07 | True  | id | False | 2    | True  | True  | 720      | 720     | 3    | 1   |
| 08 | True  | id | False | []   | False | True  | 720      | 720     | 1    | 1   |
| 09 | True  | id | False | []   | True  | False | 720      | 720     | 1    | 1   |
| 10 | True  | id | False | []   | True  | True  | 720      | 720     | 1    | 1   |
| 11 | True  | id | False | []   | True  | True  | 720      | 720     | 5    | 1   |
| 12 | True  | id | False | []   | True  | True  | 0        | 0       | 1    | 1   |

### Description

* `01` - basic model created with `create_model()` and default settings
* `02` - basic model with `MULTIPROCESSING = True`
* `03` - basic model with 100 model points
* `04` - basic model with 100 model points and `MULTIPROCESSING = True`
* `05` - basic model with 10 model points and individual results (`AGGREGATE = False`)
* `06` - basic model with 10 model points and id column set to `mp`
* `07` - model with 3 simple variables and `OUTPUT_COLUMNS = ["a", "c"]`
* `08` - basic model with `SAVE_DIAGNOSTIC = False`
* `09` - basic model with `SAVE_OUTPUT = False`
* `10` - model with variable that is calculated backward
* `11` - model with variables forming a cycle (real estate mortgage)
* `12` - model in which runplan is used
* `13` - memory management tests
