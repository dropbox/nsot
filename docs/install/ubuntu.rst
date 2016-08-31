######
Ubuntu
######

This installation guide assumes that you are running Ubuntu version 12.04,
14.04, or 16.04 on your machine, and are wanting to install NSoT. This guide
will help you install NSoT and then run it locally from a browser window.

Installation
============

To ensure your Ubuntu installation is up to date, please update it. Open a
command prompt and run the following:

.. code-block:: bash

    $ sudo apt-get -y update

Once your machine is up to date, we need to install development libraries to
allow NSoT to build:

.. code-block:: bash

    $ sudo apt-get -y install build-essential python-dev libffi-dev libssl-dev

The Python Pip installer and the git repository management tools are needed
too. We'll go ahead and get those next:

.. code-block:: bash

    $ sudo apt-get --yes install python-pip git

.. code-block:: bash

    $ sudo pip install nsot 

Now you are ready to follow the :doc:`../quickstart` starting at step 2!
