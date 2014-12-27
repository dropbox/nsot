# nsot

[![Build Status](https://travis-ci.org/dropbox/nsot.png?branch=master)](https://travis-ci.org/dropbox/nsot)
[![Documentation Status](https://readthedocs.org/projects/nsot/badge/?version=latest)](https://readthedocs.org/projects/nsot/?badge=latest)

## Warning

AThis project is still very much in flux and likely to have database changes without
migration support for the time being. Also some documentation may describe steps not yes possible.

### Description

NSoT is a Network Source of Truth API and FE for managing Network Assets.

Currently only IP Address Management on on the road-map but it will evolve
into more over time.


### Installation

New versions will be updated to PyPI pretty regularly so it should be as easy
as:

```bash
$ pip install nsot
```

### Development

I suggest setting up your test environment in a virtual environment. If you use
virtualenvwrapper you can just do

```bash
$ mkvirtualenv nsot
```

After that, clone the repo into whichever directory where you do development
and install the dependencies.

```bash
$ git clone git@github.com:dropbox/nsot.git
$ cd nsot
$ pip install -r requirements-dev.txt
$ python setup.py develop
```
#### Running Tests
All tests will automatically be run on Travis CI when pull requests are sent
however it's beneficial to run the tests often during development.

```bash
py.test -v tests/
```

#### Running a Test instance

NSoT runs behind a reverse proxy that handles Authentication and so expects
a valid, authenticated, user account. I've included a test proxy for running
on development instances.

```bash

# Setup the database.
nsot-ctl -vvv -c config/dev.yaml sync_db

# Run the development reverse proxy
nsot-ctl -vv -c config/dev.yaml user_proxy $USER@localhost

# Run the frontend server
nsot-server --config=config/dev.yaml -vv

```
