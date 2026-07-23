from pathlib import Path

from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize
import numpy as np


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

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
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=["cashflower", "cashflower.*"]),
    ext_modules=extensions,
    package_data={
        "cashflower": ["cython/*.pyx", "cython/*.c"],
        "cashflower.model_tpl": ["*.py"],
    },
    project_urls={
        "Source": "https://github.com/acturtle/cashflower",
        "Tracker": "https://github.com/acturtle/cashflower/issues",
        "Documentation": "https://cashflower.acturtle.com",
        "Cheat sheet": "https://www.acturtle.com/static/pdf/cheat_sheet.pdf",
    },
)
