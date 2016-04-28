########
Tutorial
########

Here's how to use NSoT.

This document assumes that you've already have an instance of NSoT installed,
configured, and running on your system. If you don't, please either check out
the :doc:`quickstart` or head over to the full-blown :doc:`installation` guide
and then return here.

First Steps
===========

.. important::
    Because this is a work-in-progress, we're going to use the command-line
    utility provided by the official NSoT client to get you acquainted with
    NSoT.

Install the Client
------------------

First things first, you'll need to install `pyNSoT
<https://pynsot.readthedocs.io>`_, the official Python API client and CLI
utility:

.. code-block:: bash

    $ pip install pynsot

Configure the Client
--------------------

After you've installed the client, please follow the `pyNSoT Configuration
<http://pynsot.readthedocs.io/en/latest/config.html>`_ guide to establish a
``.pynsotrc`` file.

Using the Command-Line
======================

Once you've got a working ``nsot`` CLI setup, please follow the `pyNSoT
Command-Line <http://pynsot.readthedocs.io/en/latest/cli.html>`_ guide. This
will get you familiarized with the basics of how NSoT works.

Understanding the Data Model
============================

NSoT has a relatively simple data model, but the objects themselves can be
quite sophisticated. Familiarize yourself with the :doc:`models`.

Using the REST API
==================

Familiarize yourself with the basics of the :doc:`api/rest`.

Administering the Server
========================

Familiarize with the ``nsot-server`` command that is used to manage your server
instance by checking out the :doc:`admin` guide.
