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

.. important::
    These instructions are still a work in progress and might mention Vagrant.
    If that's confusing, please run the basic install steps for your platform
    of choice, and then refer back to the :doc:`quickstart` guide.

.. toctree::
    :maxdepth: 1
    :glob:

    install/*

Vagrant Install Instructions
============================

These guides go into detail on how to get running NSoT using Vagrant. There are
Vagrantfiles for a variety of platforms, in case you want to see what NSoT
might be like running on a platform relevant to your environment.

.. warning::
    These are being cleaned up as we prepare for the 1.0 release! Proceed with
    caution!

.. toctree::
    :maxdepth: 1
    :glob:

    vagrant/*

Docker Install Instructions
===========================

Want to use Docker? More on this later. For now you may look at the ``docker``
directory at the top of the repository on GitHub, or if you're feeling plucky,
check out the contents of :doc:`dockerfile`.

Demo
====

If you would like to run the demo, make sure you've got NSoT installed, change
to the ``demo`` directory and run:

.. warning::
    This demo is a little bit out of date, but still technically works.
    It is being cleaned up as we prepare for the 1.0 release! Proceed with
    caution!

.. code:: bash

   $ ./run_demo.sh
