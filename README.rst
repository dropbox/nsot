####
nsot
####

|Build Status| |Documentation Status|

Network Source of Truth (NSoT) is a API and web application front-end for
managing network entities.

Warning
=======

This project is stable and fully unit-tested, however as it is pre-1.0 it is
still very much in flux and likely to have backwards-incompatible API changes
for the time being. Also some documentation may describe steps not yet
possible, or in some cases possible steps may not be fully documented.

Description
===========

NSoT is designed to be a source of truth database and repository for tracking
inventory and metadata of network entities to ease management and automation of
network infrastructure.

Currently only IP address management (IPAM), device inventory, and network
interfaces is on the road-map but it will evolve into more over time.

For more information please, see the documentation.

Documentation
=============

The latest documentation will always be available at
http://nsot.readthedocs.org/en/latest/

Interactive API documentation can be found at ``/docs/`` on a running NSoT
server.

Installation
============

New versions will always be uploaded to PyPI regularly so it should be as easy as:

.. code:: bash

    $ pip install nsot

Development
===========

**Note:** You'll need to have a reasonably recent version of `npm
<https://github.com/npm/npm>`_ to build front-end dependencies. (Minimum
version tested is ``1.3.24``)

We suggest setting up your test environment in a Python `virtualenv
<https://virtualenv.pypa.io>`_:

.. code:: bash

    $ virtualenv nsot
    $ source nsot/bin/activate

Or, if you use `virtualenvwrapper
<https://virtualenvwrapper.readthedocs.org>`_:

.. code:: bash

    $ mkvirtualenv nsot

If you haven't already, make sure you `set up git
<https://help.github.com/articles/set-up-git/>`_ and `add an SSH key to your
GitHub account <https://help.github.com/articles/generating-ssh-keys/>`_ before
proceeding!

After that, clone the repository into whichever directory you use for
development and install the dependencies:

.. code:: bash

    $ git clone git@github.com:dropbox/nsot.git
    $ cd nsot
    $ pip install -r requirements-dev.txt
    $ python setup.py develop

Running a Test instance
-----------------------

For developement and testing, it's easiest to run NSoT behind a reverse proxy
that handles authentication and sends a username via a `special HTTP header
<http://nsot.readthedocs.org/en/latest/api.html#user-authentication-header>`_.
We've included a test proxy for running on development instances.

To get started, follow these steps:

.. code:: bash

    # Initialize the config
    $ nsot-server init

    # Setup the database.
    $ nsot-server upgrade

    # Run the development reverse proxy (where $USER is the desired username)
    $ nsot-server user_proxy $USER

    # (In another terminal) Run the front-end server, remember to activate your
    # virtualenv first if you need to
    $ nsot-server start

**Note:** This quick start assumes that you're installing and running NSoT on
your local system (aka `localhost`).

Now, point your web browser to http://localhost:8888 and explore the
`documentation <https://nsot.readthedocs.org>`_!

Running Tests
-------------

All tests will automatically be run on Travis CI when pull requests are sent.
However, it's beneficial to run the tests often during development:

.. code:: bash

    $ py.test -v tests/

Working with database migrations
--------------------------------

If you make any changes to the database models you'll need to generate a new
migration. We use Django's built-in support for database migrations underneath,
so for general schema changes is should be sufficient to just run:

.. code:: bash

    $ nsot-server makemigrations

This will generate a new schema version. You can then sync to the latest
version:

.. code:: bash

    $ nsot-server migrate

Working with docs
-----------------

Documentation is generated using `Sphinx <http://sphinx-doc.org/>`_. If you
just want to build and view the docs | you cd into the ``docs`` directory and
run ``make html``. Then point your browser | to
``docs/\_build/html/index.html`` on your local filesystem.

If you're actively modifying the docs it's useful to run the autobuild server:

.. code:: bash

    $ sphinx-autobuild docs docs/_build/html/

This will start a server listening on a port that you can browse to and will be
automatically reloaded when you change any rst files. One downside of this
approach is that is doesn't refresh when docstrings are modified.

Front-end development
---------------------

We use a combination JavaScript utilities to do front-end development:

+ `npm <https://www.npmjs.com/>`_ - npm is used to manage our build dependencies
+ `bower <http://bower.io/>`_ - bower to manage our web dependencies
+ `gulp <http://gulpjs.com/>`_ - gulp for building, linting, testing

**Note:** You do not have to install these yourself! When you run ``setup.py develop``,
it will install and build all front-end components for you!

Adding new build dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the most part you shouldn't need to care about these details though if you
want to add new build dependencies, for example `gulp-concat
<https://github.com/contra/gulp-concat>`_, you would run the followiing:

.. code:: bash

    # Install gulp-concat, updating package.json with a new devDependency
    $ npm install gulp-concat --save-dev

    # Writes out npm-shrinkwrap.json, including dev dependencies, so consistent
    # build tools are used
    $ npm shrinkwrap --dev

Adding new web dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding new web dependencies are done through bower:

.. code:: bash

    # Install lodaash, updating bower.json with the new dependency
    $ bower install lodash --save

Unfortunately, bower doesn't have a shrinkwrap/freeze feature so you'll
want to update the version string to make the version explicit for repeatable
builds.

We make use of bower's "main file" concept to distribute only "main" files.
Most packages don't consider consider the minified versions of their project to
be their main files so you'll likely also need to update the ``overrides``
section of ``bower.json`` with which files to distribute.

Demo
====

If you would like to run the demo, make sure you've got NSoT installed, change
to the ``demo`` directory and run:

.. code:: bash

   $ ./run_demo.sh

Support
=======

For the time being the best way to get support, provide feedback, ask
questions, or to just talk shop is to find us on IRC at ``#nsot`` on Freenode
(**irc://irc.freenode.net/nsot**).

.. |Build Status| image:: https://travis-ci.org/dropbox/nsot.png?branch=master
   :target: https://travis-ci.org/dropbox/nsot
.. |Documentation Status| image:: https://readthedocs.org/projects/nsot/badge/?version=latest
   :target: https://readthedocs.org/projects/nsot/?badge=latest

See Also
========

+ `pynsot <https://github.com/dropbox/pynsot>`_ - Python client library and
  command-line utility for the Network Source of Truth REST API.
