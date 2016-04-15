####
SuSe
####

This installation guide assumes that you have installed SuSe 13 on your
machine, and are wanting to install NSoT. This guide will help you install NSoT
and then run it locally from a browser window.

Installation
============

To ensure your SuSe installation is up to date, please update it. We'll begin
by opening a command prompt. Make sure your certificates are properly
installed, or use this certificate:

.. code-block:: bash

    $ wget --no-check-certificate 'https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub' -O /home/vagrant/.ssh/authorized_keys

Now we'll install the prerequisite software with zypper:

.. code-block:: bash

    $ sudo zypper --non-interactive in python-devel gcc gcc-c++ git libffi48-devel libopenssl-devel python-pip 

Next you'll need to upgrade Pip and security addons:

.. code-block:: bash

    $ sudo pip install --upgrade pip
    $ sudo pip install requests[security]

Now we are ready to install NSoT:

.. code-block:: bash

    $ sudo pip install nsot

SuSe Firewall
-------------

To access NSoT from a local browser we'll need to turn off the security for
this demo:

.. code-block:: bash

    $  sudo /sbin/service SuSEfirewall2_setup stop 

For production installations we reccomend adding a rule to your iptables for
NSoT on ports ``8990/tcp`` (or the port of your choosing).

Now you are ready to follow the :doc:`../quickstart` starting at step 2!
