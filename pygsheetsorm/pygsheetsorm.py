# -*- coding: utf-8 -*-
# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

"""
Classes to interact with a google spreadsheet via a model
with attributes that automatically map to column headers
"""
import datetime
import re
import logging
import pygsheets
import six
from googleapiclient.errors import HttpError
from retrying import retry

LOG = logging.getLogger(__name__)


class CellConverter(object):
    """See BasicCellConverter for how to implement."""

    pass


class BasicCellConverter(CellConverter):
    def from_cell(self, cell, property_name):
        # In most cases, value_unformatted is what we want.
        # It can return unicode, bool, int, float based on
        # type set in google sheet.
        value = cell.value_unformatted
        # format is either a unicode string or an enum from pygsheets
        format_type = cell.format[0]
        if isinstance(format_type, six.string_types):
            if u"DATE" in format_type or u"TIME" in format_type:
                # Need to convert google sheet return value (which is based on excel)
                # to a real datetime https://stackoverflow.com/a/47508307
                cell_datetime = datetime.datetime(
                    year=1899, month=12, day=30
                ) + datetime.timedelta(days=value)
                # Round the microseconds
                if cell_datetime.microsecond >= 500000:
                    cell_datetime = cell_datetime.replace(
                        second=cell_datetime.second + 1, microsecond=0
                    )
                else:
                    cell_datetime = cell_datetime.replace(microsecond=0)
                if format_type == u"DATE_TIME":
                    return cell_datetime
                elif format_type == u"DATE":
                    return cell_datetime.date()
                elif format_type == u"TIME":
                    return cell_datetime.time()
        return value

    def to_cell(self, cell, property_name, value):
        cell.value = str(value)


def retry_if_over_write_quota(exception):
    """Returns True if the exception is an insufficient tokens for quota errorr"""
    over_quota = isinstance(
        exception, HttpError
    ) and "Insufficient tokens for quota" in str(exception)
    if over_quota:
        LOG.debug("Encountered over quota exception")
    return over_quota


class ModelMetadata(object):
    """Hold metadata for a Model. This data is primarily used by
       the Repository

    Args:
      repository (Repository): Repository to associate with
      model (Model): Which Model to associate with
      cell_converter (CellConverter): Cell converter to use when
                                     setting values.

    """

    def __init__(self, repository, model, cell_converter):
        self.repository = repository
        self.model = model
        self.cell_converter = cell_converter
        # Store mappings of property name to column number
        self.property_to_column = {}
        self.property_to_cell = {}
        self.reset_modified_properties()

    def add_cell(self, property_name, cell):
        """Used by Repository to populate starting state of Model.
           This bypasses setattr so nothing is marked as modified.

        Args:
          name (str): name of property (must be valid python property name)
          cell (pygsheets.Cell): Cell property corresponds to
          value: value of property
        """
        self.property_to_cell[property_name] = cell
        self.property_to_column[property_name] = cell.col
        converted_value = self.cell_converter.from_cell(
            cell=cell, property_name=property_name
        )
        self.model.__dict__[property_name] = converted_value

    def set_modified_property(self, property_name):
        """Mark a property as modified. Used to determine
           what properties will need to be saved.

        Args:
          property_name (str): property name
        """
        self.modified_properties.add(property_name)

    def reset_modified_properties(self):
        """On init, or save, reset our modified properties."""
        self.modified_properties = set([])

    def get_modified_properties(self):
        """Get properties that have been modified.
        Returns:
          set: modified properties

        """
        return self.modified_properties

    def save(self):
        # TODO: Add batch save code
        for property_name in self.get_modified_properties():
            self._save_property(property_name)
        self.reset_modified_properties()

    @retry(
        wait_exponential_multiplier=1000,
        wait_exponential_max=60000,
        retry_on_exception=retry_if_over_write_quota,
    )
    def _save_property(self, property_name):
        """Save property (cell) with exponential backoff retry up to 60 seconds.
           Retry specifically happens if you hit API quota.

        Args:
          property_name (str): property name to save
        """
        value = self.model.__dict__[property_name]
        cell = self.property_to_cell[property_name]
        # Setting the value on the cell will save the cell
        self.cell_converter.to_cell(cell=cell, property_name=property_name, value=value)


class Model(object):
    """Model is used to map a row in a spreadsheet to an object
    with properties that map to column names. Models should
    only be created by Repository.

    Args:
      repository (Repository): Repository to associate with
      cell_convert (int): row number Model corresponds to
    """

    # TODO refactor repository out, not really needed
    def __init__(self, repository, cell_converter=None):
        if not cell_converter:
            cell_converter = BasicCellConverter()
        # Uppercase breaks conventions, but guarantees no collisions with
        # customer fields
        self.Metadata = ModelMetadata(
            repository=repository, model=self, cell_converter=cell_converter
        )

    def __setattr__(self, key, value):
        if key != "Metadata":  # metadata is special
            if not hasattr(self, key):
                raise TypeError("No column corresponds with name {}".format(key))
            if self.__dict__[key] != value:
                # Only set modified if value has actually changed
                self.Metadata.set_modified_property(key)
        object.__setattr__(self, key, value)

    def __repr__(self):
        repr_str = "<Model "
        for column_number, property_name in six.iteritems(
            self.Metadata.repository._col_to_property_name
        ):
            repr_str += '[{}:{}="{}"], '.format(
                column_number, property_name, self.__dict__[property_name]
            )
        repr_str = repr_str.rstrip(" ,") + ">"
        return repr_str

    def Save(self):
        """Save model back to row in spreadsheet.
           Only properties that have changed will be saved.
           Uppercase method guarantees no collisions with customer
           data.
        """
        self.Metadata.save()


class SpreadsheetException(Exception):
    """The exception class for connecting to Google API"""


class Repository(object):
    """This Repository is used to access a sheet and return
    Model objects which represent each row in the sheet.
    The first row is assumed to be the header. Column
    values from the first row will be lowercased and
    underscores replacing characters to create
    the property names.

    Args:
      pygsheets_worksheet (pygsheets.Worksheet): Worksheet to read/write fro
      cell_converter: cell_converter allows you to customize the value that is set
          on the Model for a given property as well as when the value is saved back
          to the cell. The default is None which means a BasicCellConverter will
          be instantiated and used.
          A converter is an object with a two methods.
          obj.from_cell(pygsheets.Cell, str) and obj.to_cell(pygsheets.Cell, str, str).
          from_cell will be called to populate the value of a property on Model. It
          is called for each corresponding cell to property name. Arguments passed
          are the cell and  property_name.
          to_cell is called to update the cell with the value currently set on the
          Model. It is called with pygsheets.Cell, property_name and the current
          value set on the Model for the given property_name.
    Returns:
      Repository

    """

    def __init__(self, pygsheets_worksheet, cell_converter=None):
        self.worksheet = pygsheets_worksheet
        self._col_to_property_name = {}
        self._set_header_mappings()
        # We will cache the models
        self._models = []
        # If no cell_converter given, default to our basic one
        if not cell_converter:
            cell_converter = BasicCellConverter()
        self._cell_converter = cell_converter

    def _get_property_name_from_column_header(self, column_header):
        """Convert a column name into a valid python property.

        Args:
          column_header (str): text from column header

        Returns:
          str: lowercase alphanumeric with underscores replacing invalid chars
        """
        property_name = column_header.lower()
        # Swap non-alphanumeric with underscores
        property_name = re.sub("[^0-9a-zA-Z]+", "_", property_name)
        # Swap leading numbers with underscores
        property_name = re.sub("^[0-9]+", "_", property_name)
        return property_name

    def _set_header_mappings(self):
        """Populate a dict to map column numbers to python property names."""
        header_row = self.worksheet.get_row(
            1, include_tailing_empty=False, returnas="cells"
        )
        for cell in header_row:
            property_name = self._get_property_name_from_column_header(cell.value)
            self._col_to_property_name[cell.col] = property_name

    @classmethod
    def get_repository_with_creds(
        cls, service_account_file, spreadsheet_id, sheet_name="Sheet1"
    ):
        """Factory method to return a Repository given signed crednentials,
        spreadsheet id, and name of sheet.

        Args:
          service_account_file (str): Service account key file (JSON) from google
              https://pygsheets.readthedocs.io/en/stable/authorizing.html#signed-credentials
          spreadsheet_id (str): The ID of the google spreadsheet to retrieve data from.
          sheet_name (str): Name of sheet in spreadhseet to read/write to.
                            Default value = "Sheet1"

        Returns:
          Repository: Repository created with arguments

        """
        try:
            client = pygsheets.authorize(service_account_file=service_account_file)
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet_by_title(sheet_name)
            return cls(pygsheets_worksheet=worksheet)
        except HttpError as err:
            if "Requested entity was not found" in err._get_reason():
                raise SpreadsheetException(
                    "Error connecting to Google Sheets. " "Check your spreadsheet ID."
                )
            raise

    def get_all(self, lambda_filter=None):
        """Get all rows from sheet as Model objects. A filter can be provided to
        limit results. First row is assumed to be header and is not returned.
        All records are initially cached so subsequent calls can be made with
        or without a filter and no data will be pulled from the sheet.

        Args:
          lambda_filter (function): Lambda function which will filter list
              (Default value = None)

        Returns:
          list: Model objects that correspond to each row in the sheet

        """
        # Only get new models if none are cached
        if not self._models:
            rows = self.worksheet.get_all_values(
                include_tailing_empty=False,
                include_tailing_empty_rows=False,
                returnas="cells",
            )
            # Skip header row and iterate over cells
            for row in rows[1:]:
                model = self._get_model_from_row(row)
                self._models.append(model)
        if lambda_filter:
            return list(filter(lambda_filter, self._models))
        return self._models

    def _get_model_from_row(self, row):
        """Given a list of pygsheets.Cell objects, return a Model.

        Args:
          row (list): list of pygsheets.Cell objects
        Returns:
          Model: Model object populated from row
        """
        model = Model(repository=self, cell_converter=self._cell_converter)

        # Empty cells don't get returned so we create empties to work with
        columns_to_add = set(list(self._col_to_property_name.keys()))
        for cell in row:
            row_number = cell.row  # When we fill in emptyies, we need this
            try:
                columns_to_add.remove(cell.col)
            except KeyError:
                # Ignore cells that don't correspond to column headers
                pass
        for column_number in columns_to_add:
            cell_pos = (row_number, column_number)
            empty_cell = pygsheets.Cell(cell_pos, worksheet=self.worksheet)
            row.append(empty_cell)

        for cell in row:
            try:
                property_name = self._col_to_property_name[cell.col]
                model.Metadata.add_cell(cell=cell, property_name=property_name)
            except KeyError:
                # Don't set properties for any values
                # we don't have a mapping for
                # there was no header
                pass
        return model
