import os
import shutil


from .utils import replace_in_file


def create_model(model):
    """Create a folder structure for a model.

    Copies the whole content of the model_tpl folder and changes templates to scripts.

    Parameters
    ----------
    model : str
        Name of the model to be added.

    """
    template_path = os.path.join(os.path.dirname(__file__), "model_tpl")
    current_path = os.getcwd()

    shutil.copytree(template_path, model)

    # Some scripts needs words replacements
    run_file = os.path.join(current_path, model, "run.py-tpl")
    model_file = os.path.join(current_path, model, "model.py-tpl")
    replace_in_file(run_file, "{{ model }}", model)
    replace_in_file(model_file, "{{ model }}", model)

    # Remove -tpl from template
    os.rename(run_file, run_file[:-4])
    os.rename(model_file, model_file[:-4])
