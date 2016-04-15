######
Fedora
######

This installation guide assumes that you have installed Fedora 22 on your
machine, and are wanting to install NSoT. This guide will help you install NSoT
and then run it locally from a browser window.

Installation
============

To ensure your Fedora installation is up to date, please update it. 
Once complete, open a command prompt and run the following:

.. code-block:: bash

    $ sudo dnf -y install gcc gcc-c++ libffi libffi-devel python-devel openssl-devel 
    $ sudo dnf -y gcc-plugin-devel make automake kernel kernel-devel psmisc
    $ sudo dnf -y install python2-devel

Next you'll need to upgrade Pip to the latest version:

.. code-block:: bash

    $ sudo pip install --upgrade pip

Now we are ready to install NSoT:

.. code-block:: bash

    $ sudo pip install nsot

Now you are ready to follow the :doc:`../quickstart` starting at step 2!
