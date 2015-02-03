# nsot

[![Build Status](https://travis-ci.org/dropbox/nsot.png?branch=master)](https://travis-ci.org/dropbox/nsot)
[![Documentation Status](https://readthedocs.org/projects/nsot/badge/?version=latest)](https://readthedocs.org/projects/nsot/?badge=latest)

## Warning

This project is still very much in flux and likely to have database changes without
migration support for the time being. Also some documentation may describe steps not yet possible.

### Description

NSoT is a Network Source of Truth API and FE for managing Network Assets.

Currently only IP Address Management is on the road-map but it will evolve
into more over time.


### Installation

New versions will be updated to PyPI pretty regularly so it should be as easy
as:

```bash
$ pip install nsot
```

### Documentation

The latest documentation will always be available at http://nsot.readthedocs.org/en/latest/

### Development

I suggest setting up your test environment in a virtual environment. If you use
virtualenvwrapper you can just do

```bash
$ mkvirtualenv nsot
```

After that, clone the repo into whichever directory you use for development
and install the dependencies.

```bash
$ git clone git@github.com:dropbox/nsot.git
$ cd nsot
$ pip install -r requirements-dev.txt
$ python setup.py develop
```
#### Running Tests
All tests will automatically be run on Travis CI when pull requests are sent.
However, it's beneficial to run the tests often during development.

```bash
py.test -v tests/
```

#### Running a Test instance

NSoT runs behind a reverse proxy that handles Authentication and so expects
a valid, authenticated, user account. I've included a test proxy for running
on development instances.

```bash

# Setup the database.
nsot-ctl -vvv -c config/dev.yaml migrations latest

# Run the development reverse proxy
nsot-ctl -vv -c config/dev.yaml user_proxy

# Run the frontend server
nsot-server --config=config/dev.yaml -vv

```

#### Working with migrations

If you make any changes to the models you'll want to generate a new migration.
We use alembic for migrations underneath but for general schema changes is
should be sufficient to just run

```bash

nsot-ctl -vvv -c config/dev.yaml migrations revision

```

This will generate a new schema version. You can then sync to the latest version
with

```bash

nsot-ctl -vvv -c config/dev.yaml migrations latest

```

#### Working with docs

Documentation is done with Sphinx. If you just want to build and view the docs you
cd into the `docs` directory and run `make html`. Then point your browser to
`docs/\_build/html/index.html` on your local filesystem.

If you're actively modifying the docs it's useful to run the autobuild server like
so:

```bash
sphinx-autobuild docs docs/_build/html/
```

This will start a server listening on a port that you can browse to and will
be automatically reloaded when you change any rst files. One downside of this
approach is that is doesn't refresh when docstrings are modified.

#### Managing frontend dependencies

Frontend dependencies are managed through `bower`, however to ensure we always have
a consistent build we checkin the dependencies. We make use of `bower-installer` to
limit the depencies down to their core components to avoid checking in various
README, src, or build artifact files.
