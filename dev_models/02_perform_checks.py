import os
import pandas as pd
import shutil
import subprocess

from cashflower import create_model


def basic_check(model_name):
    """Run model and ensure that:
    - there are three new files in the output folder,
    - the new output has the same data as previous one.
    """
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

    # Perform checks
    print("\nCheck 1: There are 3 new files in the output folder.", end=" ")
    assert num_files1 == num_files2 - 3
    print("OK")

    print("Check 2: Output did not change.", end=" ")
    first_output = pd.read_csv(f"output/{first_output_file}")
    last_output = pd.read_csv(f"output/{last_output_file}")
    assert first_output.equals(last_output)
    print("OK")

    # Change directory back
    os.chdir("..")


def check_dev_model_00():
    """Check creating a new model from scratch."""
    model_name = "dev_model_delete_me"
    create_model(model_name)
    os.chdir(model_name)

    # Run model
    subprocess.run("python run.py", shell=True, check=True)

    # Model creates output files
    num_files = len(os.listdir("output"))
    print("\nCheck 1: There are 3 new files in the output folder.", end=" ")
    assert num_files == 3
    print("OK")

    # Change directory back and remove the folder
    os.chdir("..")
    shutil.rmtree(model_name)


def check_dev_model_01():
    basic_check("dev_model_01")
    print("\n")


def check_dev_model_02():
    basic_check("dev_model_02")
    print("\n")


def check_dev_model_03():
    basic_check("dev_model_03")
    print("\n")


def check_dev_model_04():
    basic_check("dev_model_04")
    print("\n")


def check_dev_model_05():
    basic_check("dev_model_05")
    print("\n")


def check_dev_model_06():
    basic_check("dev_model_06")
    print("\n")


def check_dev_model_07():
    basic_check("dev_model_07")

    # Output file should have 2 columns ("t", "f")
    print("Check 3: Output file has subset of columns.", end=" ")
    output_files = [f for f in os.listdir("dev_model_07/output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]
    last_output = pd.read_csv(f"dev_model_07/output/{last_output_file}")
    assert last_output.shape[1] == 2
    print("OK")

    # Unnecessary columns were not calculated
    print("Check 4: Unnecessary column were not evaluated.", end=" ")
    diagnostic_files = [f for f in os.listdir("dev_model_07/output") if f.endswith("diagnostic.csv")]
    last_diagnostic_file = diagnostic_files[-1]
    last_diagnostic = pd.read_csv(f"dev_model_07/output/{last_diagnostic_file}")
    assert "g" not in last_diagnostic["variable"].tolist()
    assert "h" not in last_diagnostic["variable"].tolist()
    print("OK")
    print("\n")


def check_dev_model_08():
    # Change directory to the model's folder
    working_directory = "dev_model_08"
    os.chdir(working_directory)

    # Run model and save information
    num_files1 = len(os.listdir("output"))
    subprocess.run("python run.py", shell=True, check=True)
    num_files2 = len(os.listdir("output"))
    diagnostic_files = [f for f in os.listdir("output") if f.endswith("diagnostic.csv")]

    # Perform checks
    print("\nCheck 1: There are 2 new files in the output folder.", end=" ")
    assert num_files1 == num_files2 - 2
    print("OK")

    print("Check 2: Diagnostic file has not been saved.", end=" ")
    assert len(diagnostic_files) == 0
    print("OK")

    # Change directory back
    os.chdir("..")
    print("\n")


def check_dev_model_09():
    # Change directory to the model's folder
    working_directory = "dev_model_09"
    os.chdir(working_directory)

    # Run model and save information
    num_files1 = len(os.listdir("output"))
    subprocess.run("python run.py", shell=True, check=True)
    num_files2 = len(os.listdir("output"))
    output_files = [f for f in os.listdir("output") if f.endswith("output.csv")]

    # Perform checks
    print("\nCheck 1: There are 2 new files in the output folder.", end=" ")
    assert num_files1 == num_files2 - 2
    print("OK")

    print("Check 2: Output file has not been saved.", end=" ")
    assert len(output_files) == 0
    print("OK")

    # Change directory back
    os.chdir("..")
    print("\n")


def check_dev_model_10():
    basic_check("dev_model_10")
    diagnostic_files = [f for f in os.listdir("dev_model_10/output") if f.endswith("diagnostic.csv")]
    last_diagnostic_file = diagnostic_files[-1]
    last_diagnostic = pd.read_csv(f"dev_model_10/output/{last_diagnostic_file}")

    print("Check 3: Calculation direction of the variable is backward.", end=" ")
    assert last_diagnostic.iloc[0]["calc_direction"] == -1
    print("OK")
    print("\n")


def check_dev_model_11():
    basic_check("dev_model_11")
    diagnostic_files = [f for f in os.listdir("dev_model_11/output") if f.endswith("diagnostic.csv")]
    last_diagnostic_file = diagnostic_files[-1]
    last_diagnostic = pd.read_csv(f"dev_model_11/output/{last_diagnostic_file}")

    print("Check 3: Variables form a cycle.", end=" ")
    assert last_diagnostic.loc[last_diagnostic["variable"] == "balance", "cycle"].values[0]
    print("OK")
    print("\n")


def check_dev_model_12():
    os.chdir("dev_model_12")

    # Run model and save information
    subprocess.run("python run.py --version 2", shell=True, check=True)
    output_files = [f for f in os.listdir("output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]

    # Perform checks
    print("\nCheck 1: The value gets multiplied by the runplan's shock.", end=" ")
    last_output = pd.read_csv(f"output/{last_output_file}")
    assert last_output.iloc[0]["premium"] == 150
    print("OK")

    # Change directory back
    os.chdir("..")


def check_dev_model_13():
    basic_check("dev_model_13")


def check_dev_model_14():
    basic_check("dev_model_14")

    print("Check 3: There are no difference between two approaches to PV calculation.", end=" ")
    output_files = [f for f in os.listdir("dev_model_14/output") if f.endswith("output.csv")]
    last_output_file = output_files[-1]
    last_output = pd.read_csv(f"dev_model_14/output/{last_output_file}")
    diff = (last_output["present_value1"] - last_output["present_value2"]).sum()
    assert abs(diff) < 0.1
    print("OK")


def check_dev_model_15():
    basic_check("dev_model_15")


def check_dev_model_16():
    basic_check("dev_model_16")


def check_dev_model_17():
    basic_check("dev_model_17")


def check_dev_model_18():
    basic_check("dev_model_18")


def check_dev_model_19():
    basic_check("dev_model_19")


def check_dev_model_20():
    basic_check("dev_model_20")


def check_dev_model_21():
    basic_check("dev_model_21")


if __name__ == "__main__":
    check_dev_model_00()
    check_dev_model_01()
    check_dev_model_02()
    check_dev_model_03()
    check_dev_model_04()
    check_dev_model_05()
    check_dev_model_06()
    check_dev_model_07()
    check_dev_model_08()
    check_dev_model_09()
    check_dev_model_10()
    check_dev_model_11()
    check_dev_model_12()
    check_dev_model_13()
    check_dev_model_14()
    check_dev_model_15()
    check_dev_model_16()
    check_dev_model_17()
    check_dev_model_18()
    check_dev_model_19()
    check_dev_model_20()
    check_dev_model_21()
    print("\nFinished! All checks completed successfully.")
