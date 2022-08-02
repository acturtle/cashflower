import os
import shutil


def replace_in_file(_file, _from, _to):
    # Read in the file
    with open(_file, "r") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(_from, _to)

    # Write the file out again
    with open(_file, "w") as file:
        file.write(filedata)


def create_model(model):
    """Create a folder structure for a model.

    Copy the whole content of the model_tpl folder.

    Parameters
    ----------
    model : str
        Name of the model to be added.

    Returns
    -------
    None
    """
    template_path = os.path.join(os.path.dirname(__file__), "model_tpl")
    current_path = os.getcwd()

    shutil.copytree(template_path, model)

    # Some scripts use templates
    run_file = os.path.join(current_path, model, "run.py-tpl")
    policy_file = os.path.join(current_path, model, "policy.py-tpl")
    replace_in_file(run_file, "{{ model }}", model)
    replace_in_file(policy_file, "{{ model }}", model)
    os.rename(run_file, run_file[:-4])
    os.rename(policy_file, policy_file[:-4])

    return None


