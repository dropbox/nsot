.. _configuration:

#############
Configuration
#############

.. contents::
    :local:
    :depth: 2

Configuring NSoT
================

This section describes how to get started with configuring the NSoT server.

Initializing the Configuration
------------------------------

You may generate an initial configuration by executing ``nsot-server init``. By
default the file will be created at ``~/.nsot/nsot.conf.py``. You may specify a
different location for the configuration as the argument to ``init``:

.. code-block:: bash

    nsot-server init /etc/nsot.conf.py

Specifying your Configuration
-----------------------------

If you do not wish to utilize the default location, you must provide the
``--config`` argument when executing ``nsot-server`` so that it knows where to
find it. For example, to start the server with the configuration in an
alternate location:

.. code-block:: bash

    nsot-server --config=/etc/nsot.conf.py start

You may also set the ``NSOT_CONF`` enviroment variable to the location of your
configuration file so that you don't have to provide the ``--config``
argument:

.. code-block:: bash

    $ export NSOT_CONF=/etc/nsot.conf.py
    $ nsot-server start

Sample Configuration
--------------------

Below is a sample configuration file that covers the primary settings you may
care about, and their default values.

.. literalinclude:: ../tests/test_settings.py
    :language: python

Advanced Configuration
======================

This section covers additional configuration options available to the NSoT
server and advanced configuration topics.

Database
--------

NSoT defaults to utilizing SQLite as a database backend, but supports any database
backend supported by Django. The default backends available are SQLite, MySQL,
PostgreSQL, and Oracle.

.. code-block:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'nsot.sqlite3',
        }
    }

For more information on configuring the database, please see the `official
Django database documentation
<https://docs.djangoproject.com/en/1.8/ref/settings/#databases>`_.

Caching
-------

**Note:** At this time only Interface objects are cached if caching is enabled!

NSoT includes built-in support for caching of API results. The default is to
use to the "dummy" cache that doesn't actually cache -- it just implements the
cache interface without doing anything.

.. code-block:: python

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

The cache is invalidated on any update or delete of an object. Caching can
dramatically perform read operations of databases with a large amount of
network Interface objects.

If you need caching, see the `official Django caching documentation
<https://docs.djangoproject.com/en/1.8/ref/settings/#caches>`_ on how to set
it up.
