import os
import pandas as pd
import shutil
import subprocess

from cashflower import create_model


def basic_check(model_name, num_files=1):
    # Change directory to the model's folder
    working_directory = model_name
    os.chdir(working_directory)

    # Run model and save information
    num_files1 = len(os.listdir("output"))
    subprocess.run("python run.py", shell=True, check=True)
    num_files2 = len(os.listdir("output"))
    output_files = [f for f in os.listdir("output") if f.endswith("output.csv")]
    first_output_file = output_files[0]
    last_output_file = output_files[-1]

    print("\nCheck: File(s) was created.", end=" ")
    assert num_files1 == num_files2 - num_files
    print("OK")

    print("Check: Output did not change.", end=" ")
    first_output = pd.read_csv(f"output/{first_output_file}")
    last_output = pd.read_csv(f"output/{last_output_file}")
    assert first_output.equals(last_output)
    print("OK")

    # Change directory back
    os.chdir("..")


def run_checks(model_name, num_files=1, extra_checks=None):
    basic_check(model_name, num_files)
    if extra_checks:
        extra_checks()


def check_dev_model_00():
    """Check creating a new model from scratch."""
    model_name = "dev_model_delete_me"
    create_model(model_name)
    os.chdir(model_name)

    # Run model
    subprocess.run("python run.py", shell=True, check=True)

    # Model creates output files
    num_files = len(os.listdir("output"))
    print("\nCheck 1: The output file has been created.", end=" ")
    assert num_files == 1
    print("OK")

    # Change directory back and remove the folder
    os.chdir("..")
    shutil.rmtree(model_name)


def check_dev_model_07():
    # Output file should have 2 columns ("t", "f")
    print("Check: Output file has subset of columns.", end=" ")
    output_files = [f for f in os.listdir("dev_model_07/output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]
    last_output = pd.read_csv(f"dev_model_07/output/{last_output_file}")
    assert last_output.shape[1] == 2
    print("OK")

    print("Check: Unnecessary column were not evaluated.", end=" ")
    diagnostic_files = [f for f in os.listdir("dev_model_07/output") if f.endswith("diagnostic.csv")]
    last_diagnostic_file = diagnostic_files[-1]
    last_diagnostic = pd.read_csv(f"dev_model_07/output/{last_diagnostic_file}")
    assert "g" not in last_diagnostic["variable"].tolist()
    assert "h" not in last_diagnostic["variable"].tolist()
    print("OK")


def check_dev_model_10():
    print("Check: Calculation direction of the variable is backward.", end=" ")
    diagnostic_files = [f for f in os.listdir("dev_model_10/output") if f.endswith("diagnostic.csv")]
    last_diagnostic_file = diagnostic_files[-1]
    last_diagnostic = pd.read_csv(f"dev_model_10/output/{last_diagnostic_file}")
    assert last_diagnostic.iloc[0]["calc_direction"] == -1
    print("OK")


def check_dev_model_11():
    print("Check: Variables form a cycle.", end=" ")
    diagnostic_files = [f for f in os.listdir("dev_model_11/output") if f.endswith("diagnostic.csv")]
    last_diagnostic_file = diagnostic_files[-1]
    last_diagnostic = pd.read_csv(f"dev_model_11/output/{last_diagnostic_file}")
    assert last_diagnostic.loc[last_diagnostic["variable"] == "balance", "cycle"].values[0]
    print("OK")


def check_dev_model_12():
    os.chdir("dev_model_12")

    # Run model and save information
    subprocess.run("python run.py --version 2", shell=True, check=True)
    output_files = [f for f in os.listdir("output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]

    print("\nCheck: The value gets multiplied by the runplan's shock.", end=" ")
    last_output = pd.read_csv(f"output/{last_output_file}")
    assert last_output.iloc[0]["premium"] == 150
    print("OK")

    # Change directory back
    os.chdir("..")


def check_dev_model_14():
    print("Check: There are no difference between two approaches to PV calculation.", end=" ")
    output_files = [f for f in os.listdir("dev_model_14/output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]
    last_output = pd.read_csv(f"dev_model_14/output/{last_output_file}")
    diff = (last_output["present_value1"] - last_output["present_value2"]).sum()
    assert abs(diff) < 0.1
    print("OK")


def check_dev_model_24():
    print("Check: Output file should have columns: one, two, three", end=" ")
    output_files = [f for f in os.listdir("dev_model_24/output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]
    last_output = pd.read_csv(f"dev_model_24/output/{last_output_file}")
    assert list(last_output.columns) == ["t", "one", "two", "three"]
    print("OK")

    print("Check: First row is 0, 1, 2, 3.", end=" ")
    assert last_output.iloc[0].tolist() == [0, 1, 2, 3]
    print("OK")


def check_all():
    models = {
        "dev_model_01": {},
        "dev_model_02": {},
        "dev_model_03": {},
        "dev_model_04": {},
        "dev_model_05": {},
        "dev_model_06": {},
        "dev_model_07": {"num_files": 2, "extra_checks": check_dev_model_07},
        "dev_model_08": {"num_files": 2},
        "dev_model_09": {"num_files": 2},
        "dev_model_10": {"num_files": 2, "extra_checks": check_dev_model_10},
        "dev_model_11": {"num_files": 2, "extra_checks": check_dev_model_11},
        "dev_model_13": {},
        "dev_model_14": {"extra_checks": check_dev_model_14},
        "dev_model_15": {},
        "dev_model_16": {},
        "dev_model_17": {},
        "dev_model_18": {},
        "dev_model_19": {},
        "dev_model_20": {},
        "dev_model_21": {},
        "dev_model_22": {},
        "dev_model_23": {},
        "dev_model_24": {"extra_checks": check_dev_model_24},
    }
    for model_name, settings in models.items():
        run_checks(model_name, **settings)

    # Models handled differently
    check_dev_model_00()  # test `create_model`
    check_dev_model_12()  # run with `python run.py --version 2`


if __name__ == "__main__":
    check_all()
    print("\n" + "*" * 72)
    print("Finished! All checks completed successfully.")
    print("*" * 72)
