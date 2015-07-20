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

Note: You'll need to have a reasonably recent version of [npm](https://github.com/npm/npm) to build
frontend dependencies. Minimum Version tested is `1.3.24`

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

# Initialize the config
nsot-server init

# Setup the database.
nsot-server upgrade

# Run the development reverse proxy
nsot-server user_proxy $USER

# Run the frontend server
nsot-server start

```

#### Working with migrations

If you make any changes to the models you'll want to generate a new migration.
We use Django's built-in support for migrations underneath, so for general
schema changes is should be sufficient to just run:

```bash

nsot-server makemigrations

```

This will generate a new schema version. You can then sync to the latest version
with

```bash

nsot-server migrate

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

#### Frontend development

We use a combination of npm, bower, and gulp to do frontend development. npm is used
to manage our build dependencies, bower to manage our web dependencies, and gulp
for building/linting/testing/etc.

`setup.py develop` will install and build all frontend components so for the most part
you shouldn't need to care about these details though if you want to add new build
dependencies, for example gulp-concat, you would run the followiing:

```bash
# Install gulp-concat, updating package.json with a new devDependency
npm install gulp-concat --save-dev

# Writes out npm-shrinkwrap.json, including dev dependencies, so consistent
# build tools are used
npm shrinkwrap --dev
```

Adding new web dependencies are done through bower

```bash
# Install lodaash, updating bower.json with the new dependency
bower install lodash --save
```

Unfortunately bower doesn't have a shrinkwrap/freeze feature so you'll want to update
the version string to make the version explicit for repeatable builds.

We make use of bower's "main file" concept to distribute only "main" files. Most packages
don't consider consider the minified versions of their project to be their main files so
you'll likely also need to update the `overrides` section of bower.json with which files
to distribute.
