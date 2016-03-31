Development
===========

Setting up Your Environment
---------------------------

**Note:** You'll need to have a reasonably recent version of `npm
<https://github.com/npm/npm>`_ to build front-end dependencies. (Minimum
version tested is ``1.3.24``)

We suggest setting up your test environment in a Python `virtualenv
<https://virtualenv.pypa.io>`_:

.. code-block:: bash

    $ virtualenv nsot
    $ source nsot/bin/activate

Or, if you use `virtualenvwrapper
<https://virtualenvwrapper.readthedocs.org>`_:

.. code-block:: bash

    $ mkvirtualenv nsot

If you haven't already, make sure you `set up git
<https://help.github.com/articles/set-up-git/>`_ and `add an SSH key to your
GitHub account <https://help.github.com/articles/generating-ssh-keys/>`_ before
proceeding!

After that, clone the repository into whichever directory you use for
development and install the dependencies:

.. code-block:: bash

    $ git clone git@github.com:dropbox/nsot.git
    $ cd nsot
    $ pip install -r requirements-dev.txt
    $ python setup.py develop

Running a Test Instance
-----------------------

For developement and testing, it's easiest to run NSoT behind a reverse proxy
that handles authentication and sends a username via a :ref:`special HTTP
header <api-auth_header>`. We've included a test proxy for running on
development instances.

To get started, follow these steps:

.. code-block:: bash

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

Now, point your web browser to http://localhost:8991 and explore the
`documentation <https://nsot.readthedocs.org>`_!

Running Unit Tests
------------------

All tests will automatically be run on Travis CI when pull requests are sent.
However, it's beneficial to run the tests often during development:

.. code-block:: bash

    $ py.test -v tests/

Working with Database Migrations
--------------------------------

If you make any changes to the database models you'll need to generate a new
migration. We use Django's built-in support for database migrations underneath,
so for general schema changes is should be sufficient to just run:

.. code-block:: bash

    $ nsot-server makemigrations

This will generate a new schema version. You can then sync to the latest
version:

.. code-block:: bash

    $ nsot-server migrate

Working with Docs
-----------------

Documentation is generated using `Sphinx <http://sphinx-doc.org/>`_. If you
just want to build and view the docs | you cd into the ``docs`` directory and
run ``make html``. Then point your browser | to
``docs/\_build/html/index.html`` on your local filesystem.

If you're actively modifying the docs it's useful to run the autobuild server:

.. code-block:: bash

    $ sphinx-autobuild docs docs/_build/html/

This will start a server listening on a port that you can browse to and will be
automatically reloaded when you change any rst files. One downside of this
approach is that is doesn't refresh when docstrings are modified.

Front-end Development
---------------------

We use a combination JavaScript utilities to do front-end development:

+ `npm <https://www.npmjs.com/>`_ - npm is used to manage our build dependencies
+ `bower <http://bower.io/>`_ - bower to manage our web dependencies
+ `gulp <http://gulpjs.com/>`_ - gulp for building, linting, testing

**Note:** You do not have to install these yourself! When you run ``setup.py develop``,
it will install and build all front-end components for you!

Adding New Build Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the most part you shouldn't need to care about these details though if you
want to add new build dependencies, for example `gulp-concat
<https://github.com/contra/gulp-concat>`_, you would run the followiing:

.. code-block:: bash

    # Install gulp-concat, updating package.json with a new devDependency
    $ npm install gulp-concat --save-dev

    # Writes out npm-shrinkwrap.json, including dev dependencies, so consistent
    # build tools are used
    $ npm shrinkwrap --dev

Adding New Web Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding new web dependencies are done through bower:

.. code-block:: bash

    # Install lodaash, updating bower.json with the new dependency
    $ bower install lodash --save

Unfortunately, bower doesn't have a shrinkwrap/freeze feature so you'll
want to update the version string to make the version explicit for repeatable
builds.

We make use of bower's "main file" concept to distribute only "main" files.
Most packages don't consider consider the minified versions of their project to
be their main files so you'll likely also need to update the ``overrides``
section of ``bower.json`` with which files to distribute.
