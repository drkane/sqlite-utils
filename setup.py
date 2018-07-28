from setuptools import setup, find_packages
import io
import os


def get_long_description():
    with io.open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="sqlite-utils",
    description="Python utility functions for manipulating SQLite databases",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    version="0.1",
    license="Apache License, Version 2.0",
    packages=find_packages(),
    install_requires=["click==6.7"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest==3.2.3"],
    entry_points="""
        [console_scripts]
        sqlite-utils=sqlite_utils.cli:cli
    """,
    url="https://github.com/simonw/sqlite-utils",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Database",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)