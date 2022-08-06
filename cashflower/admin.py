import os
import shutil


from .utils import replace_in_file


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
    model_file = os.path.join(current_path, model, "model.py-tpl")
    replace_in_file(run_file, "{{ model }}", model)
    replace_in_file(model_file, "{{ model }}", model)
    os.rename(run_file, run_file[:-4])
    os.rename(model_file, model_file[:-4])

    return None

