# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

import pytest
import os
from uuid import uuid4
from datetime import date, time, datetime
import pygsheets
from pygsheetsorm import Repository, Model


@pytest.fixture(scope="module")
def spreadsheet_id():
    # https://docs.google.com/spreadsheets/d/19Tz0H7Wy5EC0gNS65aSwBscmx-14s8A70RiMgsp3QfY/edit#gid=0
    return "19Tz0H7Wy5EC0gNS65aSwBscmx-14s8A70RiMgsp3QfY"


@pytest.fixture(scope="module")
def client_secret_file():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    # Generate one of these using instructions here https://pygsheets.readthedocs.io/en/latest/authorization.html
    cred_file = os.path.join(cur_dir, "..", "client_secret.json")
    if not os.path.exists(cred_file):
        message = "Could not find client_secret.json in {}.".format(cur_dir)
        pytest.fail(message)
        pytest.exit(message)
    return cred_file


@pytest.fixture(scope="module")
def people_worksheet(spreadsheet_id, client_secret_file):
    # Copy the People worksheet to one named with datetime
    # and use that for testing. Remove when done
    client = pygsheets.authorize(service_account_file=client_secret_file)
    spreadsheet = client.open_by_key(spreadsheet_id)
    src_worksheet = spreadsheet.worksheet_by_title("People")
    write_worksheet_title = str(datetime.now())
    write_worksheet = spreadsheet.add_worksheet(
        title=write_worksheet_title, src_worksheet=src_worksheet
    )
    yield write_worksheet
    spreadsheet.del_worksheet(write_worksheet)


@pytest.fixture(scope="module")
def people(spreadsheet_id, client_secret_file, people_worksheet):
    # Lets test our helper function while we're here
    repo = Repository.get_repository_with_creds(
        service_account_file=client_secret_file,
        spreadsheet_id=spreadsheet_id,
        sheet_name=people_worksheet.title,
    )
    return repo.get_all()


@pytest.fixture
def rick(people):
    return people[0]


@pytest.fixture
def morty(people):
    return people[1]


@pytest.mark.run(order=1)
@pytest.mark.parametrize(
    "attrib,rick_val,morty_val",
    [
        # String
        pytest.param("name", u"Rick Sanchez", u"Morty Smith"),
        # Boolean
        pytest.param("likes_dogs", False, True),
        # Percent
        pytest.param("savings_rate", 0.05, 0.06),
        # int
        pytest.param("age", 70, 14),
        # Dollars
        pytest.param("balance", 1050.63, 2201.90),
        # Date
        pytest.param(
            "account_opened",
            date(year=2010, month=1, day=2),
            date(year=2017, month=12, day=15),
        ),
        # Time
        pytest.param("alarm_time", time(hour=8), time(hour=6, minute=30)),
        # DateTime
        pytest.param(
            "last_transaction_timestamp",
            datetime(year=2017, month=9, day=1, hour=6, minute=34, second=21),
            datetime(year=2018, month=10, day=5, hour=21, minute=0, second=32),
        ),
    ],
)
def test_read_starting_data(rick, morty, attrib, rick_val, morty_val):
    assert getattr(rick, attrib) == rick_val
    assert getattr(morty, attrib) == morty_val


@pytest.mark.run(order=2)
@pytest.mark.parametrize(
    "attrib,rick_val,morty_val",
    [
        # String
        pytest.param("location", u"Space Prison", u"Earth"),
        # Boolean
        pytest.param("likes_dogs", True, False),
        # Percent
        pytest.param("savings_rate", 0.04, 0.05),
        # int
        pytest.param("age", 71, 15),
        # Dollars
        pytest.param("balance", 1104.16, 2334.01),
        # Date
        pytest.param(
            "account_opened",
            date(year=2010, month=1, day=3),
            date(year=2017, month=12, day=16),
        ),
        # Time
        pytest.param("alarm_time", time(hour=9), time(hour=7, minute=30)),
        # DateTime
        pytest.param(
            "last_transaction_timestamp",
            datetime(year=2018, month=3, day=1, hour=7, minute=16, second=19),
            datetime(year=2018, month=11, day=6, hour=23, minute=1, second=42),
        ),
    ],
)
def test_write_data(rick, morty, attrib, rick_val, morty_val):
    setattr(rick, attrib, rick_val)
    setattr(morty, attrib, morty_val)
    # Check values before save
    getattr(rick, attrib) == rick_val
    getattr(morty, attrib) == morty_val
    rick.Save()
    morty.Save()
    # Double check after save
    getattr(rick, attrib) == rick_val
    getattr(morty, attrib) == morty_val


class Cache(object):
    NEW_PEOPLE = None


@pytest.fixture
def new_people(client_secret_file, spreadsheet_id, people_worksheet):
    """Fixture to call after we've written data and want to verify
       it loads correctly in a new Repository."""
    if not Cache.NEW_PEOPLE:
        new_repo = Repository.get_repository_with_creds(
            service_account_file=client_secret_file,
            spreadsheet_id=spreadsheet_id,
            sheet_name=people_worksheet.title,
        )
        Cache.NEW_PEOPLE = new_repo.get_all()
    return Cache.NEW_PEOPLE


@pytest.mark.run(order=3)
@pytest.mark.parametrize(
    "attrib,rick_val,morty_val",
    [
        # String
        pytest.param("location", u"Space Prison", u"Earth"),
        # Boolean
        pytest.param("likes_dogs", True, False),
        # Percent
        pytest.param("savings_rate", 0.04, 0.05),
        # int
        pytest.param("age", 71, 15),
        # Dollars
        pytest.param("balance", 1104.16, 2334.01),
        # Date
        pytest.param(
            "account_opened",
            date(year=2010, month=1, day=3),
            date(year=2017, month=12, day=16),
        ),
        # Time
        pytest.param("alarm_time", time(hour=9), time(hour=7, minute=30)),
        # DateTime
        pytest.param(
            "last_transaction_timestamp",
            datetime(year=2018, month=3, day=1, hour=7, minute=16, second=19),
            datetime(year=2018, month=11, day=6, hour=23, minute=1, second=42),
        ),
    ],
)
def test_read_new_data(new_people, attrib, rick_val, morty_val):
    new_rick = new_people[0]
    new_morty = new_people[1]
    assert getattr(new_rick, attrib) == rick_val
    assert getattr(new_morty, attrib) == morty_val


def test_count_people(people):
    assert len(people) == 2
