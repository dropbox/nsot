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

If you install using pip, which you should, these will be installed for you
automatically. For now, here is the contents of ``requirements.txt``:

.. literalinclude::
    ../requirements.txt

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

Demo
====

If you would like to run the demo, make sure you've got NSoT installed, change
to the ``demo`` directory and run:

.. code:: bash

   $ ./run_demo.sh
