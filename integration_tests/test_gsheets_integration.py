# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

import pytest
import os
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


def test_read_names(john, jane):
    assert john.name == u"John"
    assert jane.name == u"Jane"


def test_read_booleans(john, jane):
    assert john.likes_cats is True
    assert jane.likes_cats is False
