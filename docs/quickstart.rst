###########
Quick Start
###########

Network Source of Truth is super easy to get running. If you just can't wait to
skip ahead, this guide is for you.

.. note::
    This quick start assumes a lot. If it doesn't work for you, please skip
    this and read the installation_ guide.

.. _installation: https://github.com/dropbox/nsot/blob/develop/docs/installation.rst

1. Install NSoT:

   .. code-block:: bash

       $ pip install nsot

2. Initialize the config (this will create a default config in
   ``~/.nsot/nsot.conf.py``):

   .. code-block:: bash

       $ nsot-server init

3. Create a superuser and start the server on ``8990/tcp`` (the default):

   .. code-block:: bash

       $ nsot-server createsuperuser --email admin@localhost
       Password:
       Password (again):
       Superuser created successfully.

   .. code-block:: bash

       $ nsot-server start

4. Now fire up your browser and visit http://localhost:8990!

.. image:: _static/web_login.png
   :alt: NSoT Login

5. Use the username/password created in step 3 to login.

Now, head over to the tutorial_ to start getting acquainted with NSoT!

.. _tutorial: https://github.com/dropbox/nsot/blob/develop/docs/tutorial.rst
