from setuptools import setup, find_packages
from pathlib import Path


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    author="Zuzanna",
    description="Framework for actuarial cash flow models",
    include_package_data=True,
    install_requires=[
        'pandas',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="cashflower",
    packages=find_packages(include=["cashflower", "cashflower.*"]),
    project_urls={
        'Source': 'https://github.com/acturtle/cashflower',
        'Tracker': 'https://github.com/acturtle/cashflower/issues',
        'Documentation': 'https://cashflower.readthedocs.io/en/latest/',
    },
    python_requires='>=3.9',
    url="https://github.com/acturtle/cashflower",
    version="0.2.11",
)
