import os
import shutil


def startproject(project):
    """Create folder structure for the new project.

    Parameters
    ----------
    project : str
        Name of the project
        

    Returns
    -------
    None
    """
    current_path = os.path.dirname(__file__)
    template_path = os.path.join(current_path, 'template-project')
    shutil.copytree(template_path, project)

    return None


def addmodel(project, model):
    """Create a folder structure for a model inside of the project.

    Parameters
    ----------
    project : str
        Name of the existing project.
        
    model : str
        Name of the model to be added.

    Returns
    -------
    None
    """
    current_path = os.path.dirname(__file__)
    template_path = os.path.join(current_path, 'template-model')
    shutil.copytree(template_path, os.path.join(project, model))

    return None

