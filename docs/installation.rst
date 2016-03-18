############
Installation
############

Quick Install
=============

Network Source of Truth (NSoT) should run on any Unix-like platform so long
as the dependencies are met. Provided the host is properly configured, NSoT can
be installed with a single command line entry::

    $ pip install nsot

However, we understand not all machines are already configured for NSoT. Below
we have outlined instructions for clean installs, Vagrantfiles for
single file virtual server installations, and instructions for isolating NSoT
inside Mac OS X.

Platform-Specific Installation Instructions
===========================================

These guides go into detail on how to install NSoT on a given platform.

.. toctree::
    :maxdepth: 1
    :glob:

    install/*

Vagrant Install Instructions
============================

These guides go into detail on how to get running NSoT using Vagrant. There are
Vagrantfiles for a variety of platforms, in case you want to see what NSoT
might be like running on a platform relevant to your environment.

.. toctree::
    :maxdepth: 1
    :glob:

    vagrant/*

Dependencies
============

Coming soon. For now, here is the contents of ``requirements.txt``:

.. literalinclude::
    ../requirements.txt

Demo
====

If you would like to run the demo, make sure you've got NSoT installed, change
to the ``demo`` directory and run:

.. code:: bash

   $ ./run_demo.sh
