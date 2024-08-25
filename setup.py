#!/usr/bin/env python
import logging
import os
from importlib import util
from os import path

import setuptools
from setuptools import setup

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

logger = logging.getLogger(__name__)
spec = util.spec_from_file_location(
    "ghrr.version", os.path.join("ghrr", "version.py")
)
# noinspection PyUnresolvedReferences
mod = util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore
version = mod.version  # type: ignore

# Read the contents of the requirements.txt file
with open(path.join(this_directory, "requirements.txt"), encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    extras_require={
        "dev": [
            "github3.py==4.0.1"
        ]
    },
    install_requires=requirements,
    license="Apache License 2.0",
    name="ghrr",
    version=version,
    description="GitHub Research Runner",
    author="schoster barak",
    author_email="schosterbarak@gmail.com",
    url="https://github.com/schosterbarak/ghrr",
    packages=setuptools.find_packages(exclude=["tests*", "integration_tests*"]),
    entry_points={
      'console_scripts': [
          'ghrr=ghrr.main'
      ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
