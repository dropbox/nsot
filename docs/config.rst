.. _configuration:

=============
Configuration
=============

Initializing the Configuration
------------------------------

You may generate an initial configuration by executing ``nsot-server init``. By
default the file will be created at ``~/.nsot/nsot.conf.py``. You may specify a
different location for the configuration as the argument to ``init``::

    nsot-server init /etc/nsot.conf.py

Specifying your Configuration
-----------------------------

If you do not wish to utilize the default location, you must provide the
``--config`` argument when executing ``nsot-server`` so that it knows where to
find it. For example, to start the server with the configuration in an
alternate location::

    nsot-server --config=/etc/nsot.conf.py start

Sample Configuration
--------------------

Below is a sample configuration file that covers the primary settings you may
care about, and their default values.

.. literalinclude:: ../tests/test_settings.py
    :language: python
