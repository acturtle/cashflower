Developer guide
===============

Branching policy
----------------

The picture shows the branches used in the cashflower package.

.. image:: https://acturtle.com/static/img/docs/branches.png

Branches:
    * main - the official version:
        * the same code as on PyPI
        * accepts pull requests from *develop* and *docs* branches
        * used for Read The Docs (RTD)
        * released to PyPI by setting a tag

    * develop - the development version:
        * new PyPI release candidate
        * accepts pull requests from *feature/<name>* branches
        * central point for all new features
        * no work is done here
        * greater version number than the *main* branch

    * docs - update of the main documentation:
        * supportive branch to update docs on the *main* branch
        * accepts only changes in the :code:`docs` folder
        * keeps the same version number as the *main* branch

    * feature/<name> - new functionalities:
        * place to work on new features
        * pushed to the *develop* branch (via pull request)
        * the same version number as the *develop* branch
