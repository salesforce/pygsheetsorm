

# pygsheetsorm 
[![Build Status](https://travis-ci.org/salesforce/pygsheetsorm.svg?branch=master)](https://travis-ci.org/salesforce/pygsheetsorm)

Google Sheets Object Relational Mapper

Ever wanted to be able to use a google spreadsheet like a table in your code? How about if you could get a list of objects that automatically mapped column headers into properties? Then this project is for you! This is a simple interface on top of [pygsheets](https://pygsheets.readthedocs.io/). 

# Usage

## Basic Example

Given the following google spreadsheet containing "Sheet1" with the following content:

| Name  | Location     |
|-------|--------------|
| Rick  | Earth        |
| Morty | Earth        |
| Ice-T | Alphabetrium |

```python
from __future__ import print_function
import pygsheets
from pygsheetsorm import Repository, Model

# Get a client using creds in json from google console
# Docs on how to get creds here: https://pygsheets.readthedocs.io/en/stable/authorizing.html
service_file = "./my-creds.json"
# spreadsheet_id can be grabbed from the sheet URL in your browser
spreadsheet_id = "1T63f9cwytUEyvUoI1Ce0WpBYmVYYFtbaAbtoxUrhnE8"
# The following is a helper method. You can also create a Repository
# by instantiating it directly and passing it a pygsheets.Worksheet
repo = Repository.get_repository_with_creds(service_file=service_file, 
                                            spreadsheet_id=spreadsheet_id,
                                            sheet_name="Sheet1")

# Get a list of models (turns each row into a model)
people = repo.get_all()
for person in people:
    print("{}'s location is {}".format(person.name,
                                       person.location))
# Above would print:
# Rick's location is Earth
# Morty's location is Earth
# Ice-T's location is Alphabetrium

rick = people[0]
rick.location = "Galactic Federation Prison"
rick.Save()

# The above would change the location for Rick in the google sheeet
```

## Example of boolean type conversion

Given a sheet with these contents:

| Name   | Is A Clone   |
|--------|--------------|
| Rick   | FALSE        |
| Beth   | TRUE         |
| Summer | FALSE        |
| Morty  | FALSE        |

```python
repo = Repository.get_repository_with_creds(service_file=service_file, 
                                            spreadsheet_id=spreadsheet_id,
                                            sheet_name="Sheet1")


# We can pass a filter to get all to limit what we get back
# The is_a_clone property is a bool, so we are asking for
# all people who are are clones
clone_filter = lambda x: x.is_a_clone
clones = repo.get_all(lambda_filter=clone_filter)
for clone in clones:
    if person.is_a_clone:
        print("{} is a clone!".format(person.name))

# Above would print
# Beth is a clone!

beth = clones[0]
# TRUE/FALSE are returned to us as bool types
# So we just set with a bool
beth.is_a_clone = False
# This will write FALSE into the table above
beth.Save()
```

## Example of currency and date conversion

If you cell has a date, time, or date time value, the API will return datetime.date, datetime.time or datetime.datetime.

Given this sheet:

| Name  | Blips and Chitz Balance | Expiration Date |
|-------|-------------------------|-----------------|
| Rick  | $21.50                  | 01/01/2025      |
| Morty | $19.80                  | 01/03/2025      |

```python
repo = Repository.get_repository_with_creds(service_file=service_file, 
                                            spreadsheet_id=spreadsheet_id,
                                            sheet_name="Sheet1")


people = repo.get_all()
rick = people[0]
morty = people[1]

# The if statement below evaluates to this:
# if 21.5 (float) > 19.8 (float):
if rick.blips_and_chitz_balance > morty.blips_and_chitz_balance:
    print("Wubbalubbadubdub!")

# The if statement below evaluates to this:
# if datetime.date(2025, 01, 01) < datetime.date(2025, 01, 03):
if rick.expiration_date < morty.expiration:
    # This will print
    print("Morty's balance will last longer.")
    
# Add more money!
morty.blips_and_chitz_balance += 10
# Extend the expiration date
now = datetime.datetime.now().date()
morty.expiration_date = now.replace(year=now.year + 10)
morty.Save()    
```


# Install

## Add it to your requirements.txt

```
-e git+ssh://git@github.com/salesforce/pygsheetsorm#egg=pygsheetsorm
```

## pip install it!

Note: this should be done AFTER requests, certify, etc.

```shell
pip install git+ssh://git@github.com/salesforce/pygsheetsorm#egg=pygsheetsorm
```

# Test it

`tox`

# Development

Run unit tests: `tox`

Code must be formatted with [black](https://github.com/ambv/black). You can reformat all code before submission with this tox command: `tox -e black-reformat`.

## Integration Tests

You must create a client_secrets.json in the root of the repo following [instructions](https://pygsheets.readthedocs.io/en/latest/authorization.html) from pygsheets.
