# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

import pytest
import mock
from mock import PropertyMock
import datetime
import pygsheetsorm
import pygsheets
from pygsheetsorm import Model, Repository, BasicCellConverter
from pygsheets.custom_types import FormatType


@pytest.fixture
def model():
    mock_sheet = mock.create_autospec(Repository)
    return Model(repository=mock_sheet)


def get_mock_cell(
    value, value_unformatted=None, column_number=1, row_number=1, format_type=None
):
    cell = mock.create_autospec(pygsheets.Cell)
    type(cell).col = PropertyMock(return_value=column_number)
    if format_type is None:
        format_type = (FormatType.CUSTOM, "")
    type(cell).format = PropertyMock(return_value=format_type)
    type(cell).row = PropertyMock(return_value=row_number)
    type(cell).value = PropertyMock(return_value=value)
    if value_unformatted is None:
        value_unformatted = value
    type(cell).value_unformatted = PropertyMock(return_value=value_unformatted)
    return cell


@pytest.fixture
def repo():
    mock_worksheet = mock.create_autospec(pygsheets.Worksheet)
    cell1 = mock.create_autospec(pygsheets.Cell)
    type(cell1).col = PropertyMock(return_value=1)
    cell1.value = "This is Column 1"
    cell2 = mock.create_autospec(pygsheets.Cell)
    cell2.value = "Column2 is this One"
    type(cell2).col = PropertyMock(return_value=2)
    cells = [cell1, cell2]
    mock_worksheet.get_row.return_value = cells
    return Repository(pygsheets_worksheet=mock_worksheet)


@pytest.fixture
def repo_with_empty_cells():
    # Creates a repo that is missing data in column 2
    # This simulates how pygsheets will return the cells
    #
    # | header row 1 column 1 | header row 1 column 2 |            |
    # |-----------------------|-----------------------|------------|
    # | row 2 column 1        |                       |            |
    # | row 3 column 1        |                       | not mapped |
    #
    mock_worksheet = mock.create_autospec(pygsheets.Worksheet)
    rows = []
    for row_index in range(1, 4):
        row = []
        for column_index in range(1, 3):
            value = "row {} column {}".format(row_index, column_index)
            if row_index == 1:
                value = "header " + value
            cell = get_mock_cell(
                column_number=column_index, row_number=row_index, value=value
            )
            if row_index == 1 or (row_index > 1 and column_index == 1):
                row.append(cell)
        if row_index == 3:
            # This cell doesn't correspond to a header and
            # should just be ignored
            row.append(get_mock_cell("not mapped"))
        rows.append(row)
    mock_worksheet.get_all_values.return_value = rows
    mock_worksheet.get_row.return_value = rows[0]
    repo = Repository(pygsheets_worksheet=mock_worksheet)
    return repo


@pytest.fixture
def full_repo():
    # Creates a repo with models based on the following data:
    #
    # | header row 1 column 1 | header row 1 column 2 |
    # |-----------------------|-----------------------|
    # | row 2 column 1        | row 2 column 2        |
    # | row 3 column 1        | row 3 column 2        |
    #
    mock_worksheet = mock.create_autospec(pygsheets.Worksheet)
    rows = []
    for row_index in range(1, 4):
        row = []
        for column_index in range(1, 3):
            value = "row {} column {}".format(row_index, column_index)
            if row_index == 1:
                value = "header " + value
            cell = get_mock_cell(
                column_number=column_index, row_number=row_index, value=value
            )
            row.append(cell)
        rows.append(row)
    mock_worksheet.get_all_values.return_value = rows
    mock_worksheet.get_row.return_value = rows[0]
    repo = Repository(pygsheets_worksheet=mock_worksheet)
    return repo


def test_model_repr_and_str(full_repo):
    model1 = full_repo.get_all()[0]
    expected_value = '<Model [1:header_row_1_column_1="row 2 column 1"], [2:header_row_1_column_2="row 2 column 2"]>'
    assert repr(model1) == expected_value
    assert str(model1) == expected_value


def test_row_set_incorrect_property_name(model):
    with pytest.raises(TypeError):
        model.this_doesnt_exist = "boom"


def test_model_no_properties_updated(full_repo):
    model = full_repo.get_all()[0]
    assert len(model.Metadata.get_modified_properties()) == 0


def test_model_not_modified_after_save(full_repo):
    model = full_repo.get_all()[0]
    model.header_row_1_column_1 = "row 2 column 1"
    model.Save()
    assert len(model.Metadata.get_modified_properties()) == 0
    for row in full_repo.worksheet.get_all_values():
        for cell in row:
            assert not cell.update.called


def test_repo_header_mappings(repo):
    assert repo._col_to_property_name[1] == "this_is_column_1"
    assert repo._col_to_property_name[2] == "column2_is_this_one"


def test_repo_property_name_from_column_header(repo):
    assert (
        repo._get_property_name_from_column_header("coLuMn-heAders map*to?properties")
        == "column_headers_map_to_properties"
    )
    assert (
        repo._get_property_name_from_column_header("33 not valid starting chars")
        == "__not_valid_starting_chars"
    )


def test_repo_get_all(full_repo):
    returned_rows = full_repo.get_all()
    # First row is the header, so we should only have 2
    assert len(returned_rows) == 2
    assert returned_rows[0].header_row_1_column_1 == "row 2 column 1"
    assert returned_rows[0].header_row_1_column_2 == "row 2 column 2"


def test_repo_get_all_filtered(full_repo):
    test_filter = lambda model: model.header_row_1_column_2 == "row 3 column 2"
    filtered_rows = full_repo.get_all(lambda_filter=test_filter)
    assert len(filtered_rows) == 1
    assert filtered_rows[0].header_row_1_column_1 == "row 3 column 1"


def test_repo_save(full_repo):
    model = full_repo.get_all()[0]
    model.header_row_1_column_1 = "new value"
    assert len(model.Metadata.get_modified_properties()) == 1
    assert "header_row_1_column_1" in model.Metadata.get_modified_properties()
    model.Save()
    assert len(model.Metadata.get_modified_properties()) == 0


def test_repo_with_empty_cells(repo_with_empty_cells):
    models = repo_with_empty_cells.get_all()
    models[0].header_row_1_column_1 == "row 2 column 1"
    models[0].header_row_1_column_2 == None

    models[1].header_row_1_column_1 == "row 3 column 1"
    models[1].header_row_1_column_2 == None


def test_repo_populates_boolean_in_model(full_repo):
    rows = full_repo.worksheet.get_all_values.return_value

    cell1 = get_mock_cell(
        column_number=1, row_number=4, value=u"TRUE", value_unformatted=True
    )
    cell2 = get_mock_cell(
        column_number=2, row_number=4, value=u"FALSE", value_unformatted=False
    )

    rows.append([cell1, cell2])
    full_repo.worksheet.get_all_values.return_value = rows
    models = full_repo.get_all()
    assert models[2].header_row_1_column_1 == True
    assert models[2].header_row_1_column_2 == False


@pytest.fixture
def repo_header_only():
    # Creates a repo with models based on the following data:
    #
    # | header row 1 column 1 | header row 1 column 2 |
    # |-----------------------|-----------------------|
    #
    mock_worksheet = mock.create_autospec(pygsheets.Worksheet)
    row = []
    row_index = 0
    for column_index in range(1, 3):
        value = "row {} column {}".format(row_index, column_index)
        if row_index == 1:
            value = "header " + value
        cell = get_mock_cell(
            column_number=column_index, row_number=row_index, value=value
        )
        row.append(cell)
    rows = [row]
    mock_worksheet.get_all_values.return_value = rows
    mock_worksheet.get_row.return_value = rows[0]
    repo = Repository(pygsheets_worksheet=mock_worksheet)
    return repo


def test_header_only(repo_header_only):
    models = repo_header_only.get_all()
    assert len(models) == 0
