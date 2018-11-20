# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

import pytest
import mock
from mock import PropertyMock
import datetime
import six
import pygsheetsorm
import pygsheets
from pygsheetsorm import Model, Repository, BasicCellConverter
from pygsheets.custom_types import FormatType

# TODO import this from test_pygsheetorm
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
def basic_cell_converter():
    return BasicCellConverter()


# Google Format: automatic Value TRUE Value Unformatted True Value Type <type 'unicode'> Value Unformatted Type Format <type 'bool'> Type (<FormatType.CUSTOM: None>, '')
def test_bool_converter_bool_true(basic_cell_converter):
    cell = get_mock_cell(value="TRUE", value_unformatted=True)
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == bool
    assert value == True


# Google Format: automatic Value FALSE Value Unformatted False Value Type <type 'unicode'> Value Unformatted Type Format <type 'bool'> Type (<FormatType.CUSTOM: None>, '')
def test_bool_converter_bool_false(basic_cell_converter):
    cell = get_mock_cell(value="FALSE", value_unformatted=False)
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == bool
    assert value == False


# Google Format: number Value 1.00 Value Unformatted 1 Value Type <type 'unicode'> Value Unformatted Type Format <type 'int'> Type (u'NUMBER', u'#,##0.00')
def test_basic_cell_converter_number(basic_cell_converter):
    cell = get_mock_cell(
        value=u"1.00", value_unformatted=1, format_type=(u"NUMBER", u"#,##0.00")
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == int
    assert 1 == value


# Google Format: Automatic Value 27 Value Unformatted 27 Value Type <type 'unicode'> Value Unformatted Type Format <type 'int'> Type (<FormatType.CUSTOM: None>, '')
def test_basic_cell_converter_number_automatic_int(basic_cell_converter):
    cell = get_mock_cell(value=u"27", value_unformatted=27)
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == int
    assert 27 == value


# Google Format: Automatic Value 27.5 Value Unformatted 27.5 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (<FormatType.CUSTOM: None>, ''))
def test_basic_cell_converter_number_automatic_float(basic_cell_converter):
    cell = get_mock_cell(value=u"27.5", value_unformatted=u"27.5")
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert isinstance(value, six.string_types)
    assert "27.5" == value


# Google Format: Automatic Value NaN Value Unformatted NaN Value Type <type 'unicode'> Value Unformatted Type Format <type 'unicode'> Type (<FormatType.CUSTOM: None>, '')
def test_basic_cell_converter_automatic_NaN(basic_cell_converter):
    cell = get_mock_cell(value=u"NaN", value_unformatted="NaN")
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert isinstance(value, six.string_types)
    assert u"NaN" == value


# Google Format: percent Value 10.00% Value Unformatted 0.1 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (u'PERCENT', u'0.00%')
def test_basic_cell_converter_percent(basic_cell_converter):
    cell = get_mock_cell(
        value=u"10.00%", value_unformatted=0.1, format_type=(u"PERCENT", u"0.00%")
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == float
    assert 0.1 == value


# Google Format: scientific Value 1.00E+00 Value Unformatted 1 Value Type <type 'unicode'> Value Unformatted Type Format <type 'int'> Type (u'SCIENTIFIC', u'0.00E+00')
def test_basic_cell_converter_scientific(basic_cell_converter):
    cell = get_mock_cell(
        value=u"1.00E+00", value_unformatted=1, format_type=(u"SCIENTIFIC", u"0.00E+00")
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == int
    assert 1 == value


# Google Format: Accounting Value  $ 1.00  Value Unformatted 1 Value Type <type 'unicode'> Value Unformatted Type Format <type 'int'> Type (u'NUMBER', u'_("$"* #,##0.00_);_("$"* \\(#,##0.00\\);_("$"* "-"??_);_(@_)')
def test_basic_cell_converter_accounting(basic_cell_converter):
    cell = get_mock_cell(
        value=u" $ 1.00",
        value_unformatted=1,
        format_type=(
            u"NUMBER",
            u'_("$"* #,##0.00_);_("$"* \\(#,##0.00\\);_("$"* "-"??_);_(@_)',
        ),
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == int
    assert 1 == value


# Google Format: Financial Value 1.00 Value Unformatted 1 Value Type <type 'unicode'> Value Unformatted Type Format <type 'int'> Type (u'NUMBER', u'#,##0.00;(#,##0.00)')
def test_basic_cell_converter_financial(basic_cell_converter):
    cell = get_mock_cell(
        value=u"1.00",
        value_unformatted=1,
        format_type=(u"NUMBER", u"#,##0.00;(#,##0.00)"),
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == int
    assert 1 == value


# Google Format: Currency Value $1.57 Value Unformatted 1.57 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (u'CURRENCY', u'"$"#,##0.00')
def test_basic_cell_converter_currency(basic_cell_converter):
    cell = get_mock_cell(
        value=u"$1.57",
        value_unformatted=1.57,
        format_type=(u"CURRENCY", u'"$"#,##0.00'),
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == float
    assert 1.57 == value


# Google Format: Currency Rounded Value $2 Value Unformatted 1.57 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (u'CURRENCY', u'"$"#,##0')
def test_basic_cell_converter_currency_rounded(basic_cell_converter):
    cell = get_mock_cell(
        value=u"$2", value_unformatted=1.57, format_type=(u"CURRENCY", u'"$"#,##0')
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == float
    assert 1.57 == value


# Google Format: Date Value 1/15/2018 Value Unformatted 43115 Value Type <type 'unicode'> Value Unformatted Type Format <type 'int'> Type (u'DATE', u'M/d/yyyy')
def test_basic_cell_converter_date(basic_cell_converter):
    cell = get_mock_cell(
        value=u"1/15/2018", value_unformatted=43115, format_type=(u"DATE", u"M/d/yyyy")
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == datetime.date
    assert datetime.date(2018, 1, 15) == value


# Google Format: Time Value 1:31:42 PM Value Unformatted 0.563680555556 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (u'TIME', u'h:mm:ss am/pm'))
def test_basic_cell_converter_time(basic_cell_converter):
    cell = get_mock_cell(
        value=u"1:31:42 PM",
        value_unformatted=0.563680555556,
        format_type=(u"TIME", u"h:mm:ss am/pm"),
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == datetime.time
    assert datetime.time(13, 31, 42) == value


# Google Format Date Time Value 1/16/2018 13:31:27 Value Unformatted 43116.5635069 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (u'DATE_TIME', u'M/d/yyyy H:mm:ss'))
def test_basic_cell_converter_date_time(basic_cell_converter):
    cell = get_mock_cell(
        value=u"1/16/2018 13:31:27",
        value_unformatted=43116.5635069,
        format_type=(u"DATE_TIME", u"M/d/yyyy H:mm:ss"),
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == datetime.datetime
    assert (
        datetime.datetime(year=2018, month=1, day=16, hour=13, minute=31, second=27)
        == value
    )


# Google Fromat: Date Time Value 9/21/1980 5:15:49 Value Unformatted 29485.2193171 Value Type <type 'unicode'> Value Unformatted Type Format <type 'float'> Type (u'DATE_TIME', u'M/d/yyyy H:mm:ss')
def test_basic_cell_converter_date_time2(basic_cell_converter):
    cell = get_mock_cell(
        value=u"9/21/1980 5:15:49",
        value_unformatted=29485.2193171,
        format_type=(u"DATE_TIME", u"M/d/yyyy H:mm:ss"),
    )
    value = basic_cell_converter.from_cell(cell, property_name="fake")
    assert type(value) == datetime.datetime
    assert (
        datetime.datetime(year=1980, month=9, day=21, hour=5, minute=15, second=49)
        == value
    )
