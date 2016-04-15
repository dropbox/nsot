######
CentOS
######

This installation guide assumes that you have installed CentOS 6.4 on your
machine, and are wanting to install NSoT. This guide will help you install NSoT
and then run it locally from a browser window.

Installation
============

To ensure your CentOS installation is up to date, please update it. 
Once complete, open a command prompt and run the following:

.. code-block:: bash

    $ sudo yum install -y openssl-devel python-devel libffi-devel gcc-plugin-devel
    $ sudo yum install -y epel-release
    $ sudo yum install -y python-pip

Next you'll need to upgrade Pip to the latest version with some security addons:

.. code-block:: bash

    $ sudo pip install --upgrade pip
    $ sudo pip install requests[security]

Now we are ready to Pip install NSoT:

.. code-block:: bash

    $ sudo pip install nsot

Now you are ready to follow the :doc:`../quickstart` starting at step 2!
