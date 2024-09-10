Release process
===============

|

Building the package
--------------------

1. Ensure Microsoft Visual C++ Build Tools are installed.

2. Install the required Python packages:

..  code-block::
    :caption: terminal

    pip install -r requirements.txt

3. Build the package by running:

..  code-block::
    :caption: terminal

    python setup.py build_ext
    python setup.py sdist 
    python setup.py bdist_wheel

* :code:`sdist` - creates a source distribution,
* :code:`bdist_wheel` - builds a wheel distribution.

4. Install the package locally in editable mode for testing:

..  code-block::
    :caption: terminal

    pip install -e .

|

Building the documentation
--------------------------

1. Build the documentation:

..  code-block::
    :caption: terminal

    cd docs
    make clean
    make html

2. View the documentation by opening the following file in your browser:

..  code-block::

    docs/_build/html/index.html

|

Uploading to PyPI
-----------------

1. Create a pull request to merge into the :code:`main` branch:

* :code:`feature/branch_name` --> :code:`develop`
* :code:`develop` --> :code:`main`

2. Update the version number in :code:`setup.py`:

..  code-block::

    setup(
        ...
        version="X.Y.Z",
    )

3. Publish a new release on GitHub:

* Navigate to **Releases** > **Draft a new release** > **Choose a tag** > **Create a new tag** (vX.Y.Z) > **Publish release**

4. Verify that the :code:`build_deploy` job is successful in the "Actions" tab.

If the job fails, debug the issue, delete the tag, and try again.

..  code-block::
    :caption: terminal

    git push origin --delete vX.Y.Z
