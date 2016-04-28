############
Installation
############

Dependencies
============

Network Source of Truth (NSoT) should run on any Unix-like platform that has:

+ Python 2.7
+ `pip <https://pip.pypa.io>`_

Python dependencies
-------------------

If you install using pip (which you should) these will be installed for you
automatically. For the brave, check out the contents of :doc:`requirements`.

Platform-Specific Installation Instructions
===========================================

These guides go into detail on how to install NSoT on a given platform.

.. toctree::
    :maxdepth: 1
    :glob:

    install/centos
    install/fedora
    install/macosx
    install/suse
    install/ubuntu

Virtual Machine Install Instructions
====================================

These guides go into detail on how to get running NSoT on virtual machines.

.. toctree::
    :maxdepth: 1
    :glob:

    install/docker
    install/vagrant

.. _demo:

Official Client
===============

We maintain the official NSoT client under a separate project called `pyNSoT
<https://pynsot.readthedocs.io>`_. PyNSoT provides a Python API client and an
excellent CLI utility.

If you wish to utilize NSoT from the command-line, or follow along in the
:doc:`tutorial`, you're going to need this!

Installing the client is as easy as running ``pip install pynsot``. Setup is a
breeze, too. If you run into any issues, please refer to the `official pyNSoT
documentation <https://pynsot.readthedocs.io>`_.

Demo
====

If you would like to run the demo, make sure you've got NSoT installed and that
you have a fresh clone of the NSoT repository from GitHub.

If you don't already have a clone, clone it and change into the ``nsot``
directory:

.. code-block:: bash

    $ git clone https://github.com/dropbox/nsot
    $ cd nsot

Then to switch to the  ``demo`` directory and fire up the demo:

.. code-block:: bash

   $ cd nsot/demo
   $ ./run_demo.sh

The demo will be available at http://localhost:8990/
