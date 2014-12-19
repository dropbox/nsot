# nsot

### Description

NSoT is a Network Source of Truth API and FE for managing Network Assets.

Currently only IP Address Management on on the road-map but it will evolve
into more over time.

##### Warning

This project is still very much in flux and likely to have database changes without
migration support for the time being.

### Installation

New versions will be updated to PyPI pretty regularly so it should be as easy
as:

```bash
pip install nsot
```

### Running a Test instance

NSoT runs behind a reverse proxy that handles Authentication and so expects
a valid, authenticated, user account. I've included a test proxy for running
on development instances.

The first thing you'll want to do is get your environment setup. I reccomend
setting up a virtualenv for development. Once you've activated your virtualenv
you can `pip install` either the `requirements.txt` or the `requirements-dev.txt`
file. The latter is useful if you plan to modify or run the tests and/or docs.

Creating a development instance:

```bash

# Setup the database.
PYTHONPATH=. bin/nsot-ctl -vvvc config/dev.yaml sync_db

# Run the development reverse proxy
PYTHONPATH=. bin/nsot-ctl -vvc config/dev.yaml user_proxy $USER

# Run the frontend server
PYTHONPATH=. bin/nsot-server --config=config/dev.yaml -vv

```
