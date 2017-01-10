#######
Vagrant
#######

The `Vagrantfile` in the root of this repo creates a fresh Vagrant box running
Ubuntu and NSoT.

Prerequisites
=============

To proceed you must have working installations of Vagrant and Virtualbox on
your machine. If you already have these, you may skip this step.

If you do not have a working Vagrant environment configured along with
Virtualbox, please follow the `Vagrant's "Getting Started" instructions
<https://docs.vagrantup.com/v2/getting-started/>`_ before proceeding.

Instructions
============

Provision the box
-----------------

*5-10 minutes on a fast connection*

To provision the virtual machine open a command prompt, and run the
following command from this directory:

.. code-block:: bash

    $ vagrant up

This will build a new Vagrant box, and pre-install NSoT for you.

Launch NSoT
-----------

Login to the new virtual machine via ssh:

.. code-block:: bash

    $ vagrant ssh

Start the server on ``8990/tcp`` (the default) and create a superuser when
prompted:

.. code-block:: bash

    $ nsot-server start

Point your browser to http://192.168.33.11:8990 and login!

Now you are ready to follow the :doc:`../tutorial` to start playing around.
