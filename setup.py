from setuptools import setup, find_packages
from pathlib import Path


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="cashflower",
    description="Framework for actuarial cash flow models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/acturtle/cashflower",
    author="",
    version="0.1.3",
    packages=find_packages(include=["cashflower", "cashflower.*"]),
    include_package_data=True,
    install_requires=[
        'pandas',
    ],
)
