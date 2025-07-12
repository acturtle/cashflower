from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
from pathlib import Path
import numpy as np


# Display README on PyPI page
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Cython extension
extensions = cythonize(
    [
        Extension(
            name="cashflower.cython.discount",
            sources=["cashflower/cython/discount.pyx"],
            include_dirs=[np.get_include()],
        )
    ],
    compiler_directives={"language_level": "3"},
    language_level=3,
)

setup(
    name="cashflower",
    version="0.10.5",

    author="Zuzanna Chmielewska",
    description="Framework for actuarial cash flow models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/acturtle/cashflower",
    python_requires='>=3.11',

    packages=find_packages(include=["cashflower", "cashflower.*"]),
    install_requires=[
        'pandas',
        'psutil',
        'networkx',
        'numpy'
    ],
    ext_modules=extensions,
    include_package_data=True,
    package_data={
        "cashflower": ["cython/*.pyx", "cython/*.c"],
        "cashflower.model_tpl": ["*.py"],
    },

    project_urls={
        'Source': 'https://github.com/acturtle/cashflower',
        'Tracker': 'https://github.com/acturtle/cashflower/issues',
        'Documentation': 'https://cashflower.acturtle.com',
        'Cheat sheet': 'https://www.acturtle.com/static/pdf/cheat_sheet.pdf',
    },
)
