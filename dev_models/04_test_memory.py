import os
import shutil
import subprocess


def check_dev_model_99():
    # Change directory to the model's folder
    model_name = "dev_model_99"
    working_directory = model_name
    os.chdir(working_directory)

    # Run model and save information
    subprocess.run("python run.py", shell=True, check=True)
    num_files = len(os.listdir("output"))
    output_files = [f for f in os.listdir("output") if f.endswith("output.csv")]

    # Perform checks
    print("\nCheck 1: There are 3 new files in the output folder.", end=" ")
    assert num_files == 3
    print("OK")

    # Delete output folder
    shutil.rmtree("output")

    # Change directory back
    os.chdir("..")
    print("\n")
