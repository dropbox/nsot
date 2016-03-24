Quick Start
===========

This quick start assumes a lot. If it doesn't work for you, please skip this
and read the :doc:`installation` guide.

.. note:: 
    For now you must also install mrproxy because we don't yet have a login
    page for NSoT, so to get up and running quickly you'll need to also run the
    authenticating reverse proxy.

    This is a work-in-progress and will be updated very soon!

1. Install NSoT and mrproxy::

   $ pip install nsot mrproxy

2. Initialize the config::

   $ nsot-server init

3. Start the server on ``localhost:8990`` and create a superuser when prompted::

   $ nsot-server start

4. In another terminal, start the reverse proxy on ``localhost:8991``::

   $ nsot-server user_proxy

Now fire up your browser and visit http://localhost:8991!
