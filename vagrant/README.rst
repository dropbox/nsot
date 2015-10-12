#############
Vagrant Howto
#############

What we are going to do
=======================

Install NSoT on it's own Linux environment: An Ubuntu virtual machine, with Python,
all the dev tools, SSL, etc. We use Vagrant (which requires Oracle's Virtualbox) to
control our virtual machines, and a ``Vagrantfile`` to do it all with just one
file. The ``Vagrantfile`` can be found in the same directory as this README.

Instructions
============

Download and install Vagrant
----------------------------

(5-10 minutes on a fast connection)

To proceed you must have working installations of Vagrant and Virtualbox. If
you already have these requirements, you may skip this step.

If you do not have a working Vagrant environment configured along with
Virtualbox, please follow the `Getting Started
<https://docs.vagrantup.com/v2/getting-started/>`_ instructions.

Download the Vagrantfile
------------------------

You need the Vagrantfile to tell Vagrant how to provision the virtual machine.

`Download the Vagrantfile <Vagrantfile>`_

Provision the virtual machine
-----------------------------

(5-10 minutes on a fast connection)

This will build a new Vagrant box, configure the server, update it, add
software, fix dependencies, ``pip install nsot``, add demo fixtures, and
deploy NSoT.

Open a command prompt, and run the following:

.. code:: bash

    $ vagrant up

Login to the new virtual machine
--------------------------------

Once Vagrant completes provisioning the virtual environment

To login, run the following:

.. code:: bash

    $ vagrant ssh

Start NSoT
----------

(2 minutes)

The NSoT software to is ready to operate. To start it up, run the following:

.. code:: bash

    $ cd /tmp/nsot/demo
    $ ./run_demo.sh

Your server should come online, and wait for instructions from the web
interface.

Open NSoT in your browser
-------------------------

Now you may view NSoT from your local browser of your choice. Open the
following URL, which will automatically log you in as the user
``admin@localhost``: 

http://192.168.33.11:8991

(Note that you you may need to disable some internal software firewalls to
allow a connection to this virtual machine.)
