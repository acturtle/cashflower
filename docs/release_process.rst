Release process
===============

|

Build the package
-----------------

1. Install Microsoft Visual C++ Build Tools

2. Install required Python packages

..  code-block::
    :caption: terminal

    pip install -r requirements.txt

3. Build the package

..  code-block::
    :caption: terminal

    python setup.py sdist 
    python setup.py bdist_wheel

* sdist - source distribution
* bdist_wheel - wheel distribution

4. Install package locally in an editable mode for testing

..  code-block::
    :caption: terminal

    pip install -e .

|

Build the documentation
-----------------------

1. Build the docs

..  code-block::
    :caption: terminal

    cd docs
    make clean
    make html

2. View your page by opening

..  code-block::

    docs/_build/html/index.html
