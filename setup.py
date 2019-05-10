#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

from __future__ import print_function
from setuptools import setup

setup(
    name="pygsheetsorm",
    author="Nelson Wolf",
    author_email="nelson.wolf@salesforce.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    description="Easy to use library to map a Google Sheet Worksheet to a Python object.",
    version="1.0.1",
    url="https://github.com/salesforce/pygsheetsorm",
    license="BSD 3-clause",
    packages=["pygsheetsorm"],
    zip_safe=False,
    install_requires=["pygsheets>=2", "retrying", "oauth2client"],
)
