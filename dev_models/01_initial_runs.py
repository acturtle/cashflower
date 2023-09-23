"""Run all models before development."""

import os
import subprocess


def run_model(model_name):
    working_directory = model_name
    os.chdir(working_directory)
    subprocess.run("python run.py", shell=True, check=True)
    os.chdir("..")


if __name__ == "__main__":
    num_dev_models = 14
    for num in range(1, num_dev_models+1):
        print(f"\nModel {num}:")
        run_model(f"dev_model_{num:02}")
