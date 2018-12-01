# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

import pytest
import os
from datetime import date
import pygsheets
from pygsheetsorm import Repository, Model


class Cache(object):
    PEOPLE = None


@pytest.fixture
def people():
    if not Cache.PEOPLE:
        sheet_id = "19Tz0H7Wy5EC0gNS65aSwBscmx-14s8A70RiMgsp3QfY"
        spreadsheet_id = "19Tz0H7Wy5EC0gNS65aSwBscmx-14s8A70RiMgsp3QfY"
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        # Generate one of these using instructions here https://pygsheets.readthedocs.io/en/latest/authorization.html
        service_file = os.path.join(cur_dir, "..", "client_secret.json")
        if not os.path.exists(service_file):
            message = "Could not find client_secret.json in {}.".format(cur_dir)
            pytest.fail(message)
            pytest.exit(message)
        repo = Repository.get_repository_with_creds(
            service_file=service_file,
            spreadsheet_id=spreadsheet_id,
            sheet_name="People",
        )
        Cache.PEOPLE = repo.get_all()
    return Cache.PEOPLE


@pytest.fixture
def john(people):
    return people[0]


@pytest.fixture
def jane(people):
    return people[1]


@pytest.mark.parametrize(
    "attrib,john_val,jane_val",
    [
        # String
        pytest.param("name", u"John", u"Jane"),
        # Boolean
        pytest.param("likes_cats", True, False),
        # Percent
        pytest.param("savings_rate", 0.05, 0.06),
        # int
        pytest.param("age", 20, 21),
        # Dollars
        pytest.param("balance", 1050.63, 2201.90),
        # Date
        pytest.param(
            "account_opened",
            date(year=2010, month=1, day=2),
            date(year=2012, month=12, day=15),
        ),
    ],
)
def test_read(john, jane, attrib, john_val, jane_val):
    assert getattr(john, attrib) == john_val
    assert getattr(jane, attrib) == jane_val
