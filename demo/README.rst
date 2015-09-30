#############
NSoT Demo app
#############

This is a basic server instance with a single Site full of dummy Networks,
Devices, Interfaces, and Attributes you can use to experiment.

Running the demo
================

To try out the demo, make sure you've already installed NSoT. If it's
installed in a Python virtualenv, make sure that it is activated.

Run the demo::

    $ ./run_demo.sh

This script will:

+ Set environment variable ``NSOT_CONF=./demo_settings.py`` to tell NSoT to
  read the config from there.
+ Create a demo SQLite database at ``demo.sqlite3``
+ Load the test fixtures from ``demo_fixtures.json.gz``
+ Start up the user proxy on 8991/tcp
+ Start up the web service on 8990/tcp

Explore
=======

Once it's running, point your browser to http://localhost:8991/ 

**Note:** If NSoT isn't installed on ``localhost``, substitute the IP or
hostname where it is installed.

API
---

The Browsable API can be found at http://localhost:8991/api/

Docs
----

The interactive API explorer can be found at http://localhost:8991/docs/
