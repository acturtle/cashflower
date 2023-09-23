from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
from pathlib import Path
import numpy as np


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

extensions = [
    Extension(name="cashflower.cython_code.discount",
              sources=["cashflower/cython_code/discount.pyx"],
              include_dirs=[np.get_include()]),
]

setup(
    author="Zuzanna Chmielewska",
    description="Framework for actuarial cash flow models",
    ext_modules=cythonize(extensions),
    include_package_data=True,
    install_requires=[
        'pandas',
        'psutil',
        'networkx',
        'numpy'
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="cashflower",
    packages=find_packages(include=["cashflower", "cashflower.*"]),
    project_urls={
        'Source': 'https://github.com/acturtle/cashflower',
        'Tracker': 'https://github.com/acturtle/cashflower/issues',
        'Documentation': 'https://cashflower.acturtle.com',
        'Cheat sheet': 'https://www.acturtle.com/static/pdf/cheat_sheet.pdf',
    },
    python_requires='>=3.9',
    url="https://github.com/acturtle/cashflower",
    version="0.5.4",
)
