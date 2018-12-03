# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

from __future__ import print_function
from setuptools import setup

setup(
    name="pygsheetsorm",
    version="0.1",
    description="Nice interface to Interact with a gsheet using objects",
    url="https://github.com/salesforce/pygsheetsorm",
    author="Nelson Wolf",
    author_email="nelson.wolf@salesforce.com",
    license="BSD 3-clause",
    packages=["pygsheetsorm"],
    zip_safe=False,
    install_requires=["pygsheets==1.1.4", "retrying", "oauth2client"],
)
