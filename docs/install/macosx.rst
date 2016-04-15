########
Mac OS X
########

This tutorial is designed to get a working version os NSoT installed inside a
Mac OS X system. We will install virtual environment wrappers to keep things
tidy, and isolate our installation.

Installation
============

Xcode
-----

It is assumed that you have a Mac, running OS X (written for 10.10.5), and
xcode already installed. If you don't have Xcode, please install it. You may
need to agree to a command line license. We suggest running this via command
line prior to install:

.. code-block:: bash

    $ xcodebuild -license

Prerequisites
-------------

We will put our installation of NSoT inside a Python virtual environment to
isolate the installation. To do so we need virtualenv, and virtualenvwrapper.
Open a command prompt, and install them with pip:

.. code-block:: bash

    $ pip install virtualenv
    $ pip install virtualenvwrapper

Ensure installation by running a which, and finding out where they now live:

.. code-block:: bash
 
    $ which virtualenvwrapper
    $ which virtualenv
 
Next we tell bash where these virtual environments are, and where to save the
associated data:

.. code-block:: bash

    $ vi ~/.bashrc 
 
Add these three lines:

.. code-block:: bash
 
    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Devel
    source /usr/local/bin/virtualenvwrapper.sh

Now restart bash to implement the changes:

.. code-block:: bash

    $ source ~/.bashrc 

Install NSoT
------------

NSoT will be installed via command line, into the folder of your choice. If you
don't have a preffered folder, may we suggest this:

.. code-block:: bash

    $ mkdir ~/sandbox && cd ~/sandbox
   
CD into the folder, make a virtual environment, and start it:

.. code-block:: bash
   
    $ mkvirtualenv nsot
    $ pip install 
 
Once in the folder of choice, install NSoT:

.. code-block:: bash
 
    $ pip install nsot

Now you are ready to follow the :doc:`../quickstart` starting at step 2!
