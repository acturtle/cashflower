.. cashflower documentation master file, created by
   sphinx-quickstart on Wed Nov 16 18:28:29 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


cashflower
==========

Cashflower is an open-source Python framework for actuarial cash flow models.

.. image:: https://acturtle.com/static/img/logo/turtle.png
   :width: 240px
   :align: center

Overview
^^^^^^^^

Welcome to the **cashflower** documentation, your resource for financial and actuarial cash flow modeling with Python.
Cashflower simplifies complex financial scenarios, allowing actuaries, analysts, and developers to make data-driven decisions effectively.

Cashflower's flexible framework empowers you to model various financial scenarios, from insurance policies and annuities to investment portfolios and loans.
This documentation is here to assist you in understanding and using the package to achieve your financial modeling goals.

Key features
^^^^^^^^^^^^
Cashflower's features:
 * **easy to use** - run your first cash flow model with just few commands,
 * **open source** - freely accessible to all users and available on PyPI,
 * **flexible** - integrate your project with other popular Python libraries.

Rapid start
^^^^^^^^^^^

You're just a few commands away from running your first cash flow model with cashflower:

..  code-block::
    :caption: terminal

    $ pip install cashflower
    $ python
    >>> from cashflower import create_model
    >>> create_model("mymodel")
    >>> quit()
    $ cd mymodel
    $ python run.py

Congratulations, you're all set!

Getting Started
^^^^^^^^^^^^^^^

To get started with the cashflower package, follow these steps:
 #. **Quick Start**: Get up and running quickly with the :ref:`Getting started` section.
 #. **Tutorials**: Check out our collection of practical examples in the :ref:`Tutorials` section.
 #. **Discussions**: If you encounter any issues, share your thoughts in the `Discussions <https://github.com/acturtle/cashflower/discussions>`_ page.

Cheat sheet
^^^^^^^^^^^

A cheat sheet is a quick-reference document that provides essential code snippets and syntax examples.

You can download `the Cashflower cheat sheet (PDF) <https://www.acturtle.com/static/pdf/cheat_sheet.pdf>`_.

.. image:: https://acturtle.com/static/img/docs/cheat_sheet_mini.jpg
   :target: https://www.acturtle.com/static/pdf/cheat_sheet.pdf
   :align: center


License
^^^^^^^

Cashflower is distributed under `the MIT License <https://github.com/acturtle/cashflower/blob/main/LICENSE>`_.

Contributions and Support
^^^^^^^^^^^^^^^^^^^^^^^^^

Cashflower is an open-source project, and we welcome contributions from the community.
If you encounter any issues, have suggestions, or want to contribute to the development,
please visit our `GitHub repository <https://github.com/acturtle/cashflower>`_.


|

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user_guide
   tutorials
   developer_guide
   modules
   Discussions <https://github.com/acturtle/cashflower/discussions>
