"""This is part of setuptools configuration to install the package."""
from setuptools import setup

LONG_DESCRIPTION = """This package is designed to allow you to run multiple python
scripts asynchronously. It is designed to be used in a standalone manner or as a class
within another script."""

setup(
    name="async-python-runner",
    version="0.0.1",
    description="A simple package or class to allow you to run multiple subprocesses \
        by defining the directory and main method of the target python file.",
    long_description=LONG_DESCRIPTION,
)
