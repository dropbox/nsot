#####################
Server Administration
#####################

Here's how to administer NSoT using the ``nsot-server`` command.

.. important:: 
    As NSoT is built using Django there are a number of commands available that
    we won't cover here. Any commands specific to operating NSoT, however, will
    be covered here in detail. 

Getting help
============

To see all available commands:

.. code-block:: bash

   $ nsot-server help

Generate a secret_key
=====================

Used in ``settings.py`` to do encrypt/decrypt API keys and secure cookies.

.. code-block:: bash

    $ nsot-server generate_key
    R2gasBVJKmU5ZgkrlBljyZJrLP_B6EwZ3S7k28-SkIs=

Create a superuser
==================

You need at least one superuser to administer the system.

.. code-block:: bash

   $ nsot-server createsuperuser --email admin@localhost
   Password:
   Password (again):
   Superuser created successfully.

Upgrade the database
====================

This will initialize a new database or run any pending database migrations to
an existing database.

.. code-block:: bash

   $ nsot-server upgrade
   Operations to perform:
     Synchronize unmigrated apps: django_filters, staticfiles, messages, smart_selects, rest_framework_swagger, django_extensions, rest_framework, custom_user
     Apply all migrations: admin, contenttypes, nsot, auth, sessions
   Synchronizing apps without migrations:
     Creating tables...
       Running deferred SQL...
     Installing custom SQL...
   Running migrations:
     Rendering model states... DONE
     Applying contenttypes.0001_initial... OK
     Applying contenttypes.0002_remove_content_type_name... OK
     Applying auth.0001_initial... OK
     Applying auth.0002_alter_permission_name_max_length... OK
     Applying auth.0003_alter_user_email_max_length... OK
     Applying auth.0004_alter_user_username_opts... OK
     Applying auth.0005_alter_user_last_login_null... OK
     Applying auth.0006_require_contenttypes_0002... OK
     Applying nsot.0001_initial... OK
     Applying admin.0001_initial... OK
     Applying nsot.0002_auto_20150810_1718... OK
     Applying nsot.0003_auto_20150810_1751... OK
     Applying nsot.0004_auto_20150810_1806... OK
     Applying nsot.0005_auto_20150810_1847... OK
     Applying nsot.0006_auto_20150810_1947... OK
     Applying nsot.0007_auto_20150811_1201... OK
     Applying nsot.0008_auto_20150811_1222... OK
     Applying nsot.0009_auto_20150811_1245... OK
     Applying nsot.0010_auto_20150921_2120... OK
     Applying nsot.0011_auto_20150930_1557... OK
     Applying nsot.0012_auto_20151002_1427... OK
     Applying nsot.0013_auto_20151002_1443... OK
     Applying nsot.0014_auto_20151002_1653... OK
     Applying nsot.0015_move_attribute_fields... OK
     Applying nsot.0016_move_device_data... OK
     Applying nsot.0017_move_network_data... OK
     Applying nsot.0018_move_interface_data... OK
     Applying nsot.0019_move_assignment_data... OK
     Applying nsot.0020_move_value_data... OK
     Applying nsot.0021_remove_resource_object... OK
     Applying nsot.0022_auto_20151007_1847... OK
     Applying nsot.0023_auto_20151008_1351... OK
     Applying nsot.0024_network_state... OK
     Applying nsot.0025_value_site... OK
     Applying sessions.0001_initial... OK

Reverse proxy
=============

Start an authenticating reverse proxy for use in development.

You must install MrProxy first: ``pip install mrproxy``.

.. code-block:: bash

    $ nsot-server user_proxy

Python shell
============

This will drop you into an interactive iPython shell with all of the database
models and various other utilities already imported for you. This is immensely
useful for direct access to manipulating database objects.

.. warning::
    This is an advanced feature that gives you direct access to the Django ORM
    database models. Use this very cautiously as you can cause irreparable
    damage to your NSoT installation.

.. code-block:: python

    $ nsot-server shell_plus
    # Shell Plus Model Imports
    from django.contrib.admin.models import LogEntry
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.sessions.models import Session
    from nsot.models import Assignment, Attribute, Change, Device, Interface, Network, Site, User, Value
    # Shell Plus Django Imports
    from django.utils import timezone
    from django.conf import settings
    from django.core.cache import cache
    from django.db.models import Avg, Count, F, Max, Min, Sum, Q, Prefetch
    from django.core.urlresolvers import reverse
    from django.db import transaction
    Python 2.7.8 (default, Oct 19 2014, 16:02:00)
    Type "copyright", "credits" or "license" for more information.

    IPython 3.1.0 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    In [1]:

Database shell
==============

This will drop you to a shell for your configured database. This can be very
handy for troubleshooting database issues.

.. code-block:: bash

    $ nsot-server dbshell
