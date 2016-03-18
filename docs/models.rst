Data Model
==========

The Network Source of Truth is composed of various object types that it is
important to be familiar with. This document describes each object type.

.. contents::
    :local:
    :depth: 2

Sites
-----

Sites function as unique namespaces that can contain all other objects Sites
allow an organization to have multiple instances of potentially conflicting
objects This could be beneficial for isolating corporate vs. production
environments, or pulling in the IP space of an acquisition.

Attributes
----------

Attributes are arbitrary key/value pairs that can be assigned to various
resources. If an attribute is required then additions/updates for that resource
will require that attribute be present.

Changes to attribute constraints are not retroactive. Existing resources will
not be forcefully validated until updated.

Values
~~~~~~

Values contain atttribute values. These are never directly manipulated, but
they are accessible from the API for utilty.

Resources
---------

A Resource object is any object that can have attributes. There are three
primary resource types:

+ Devices
+ Networks
+ Interfaces

Devices
~~~~~~~

A device represents various hardware components on your network such as
routers, switches, console servers, pdus, servers, etc.

Devices also support arbitrary attributes similar to Networks.

Networks
~~~~~~~~

A network resource can represent an IP Network and an IP Address. Working with
networks is usually done with CIDR notation.

Networks can have any number of arbitrary attributes as defined below.

Interfaces
~~~~~~~~~~

An interface represents a physical or logical network interface such as an
ethernet port. Interfaces must always be associated with a device. Zero or
more addresses may be assigned to an Interface, although the same address may
not be assigned to more than one interface on the same device.

Interfaces also support arbitrary attributes similar to Networks and Devices.

* Addresses TBD
* Assignments TBD

Changes
-------

All Create/Update/Delete events are logged as a Change. A Change includes
information such as the change time, user, and the full object payload after
modification.

Changes are immutable and can only be removed by deleting the entire Site.

Users
-----

Users are for logging into stuff. More on this later.

Permissions
-----------

Permissions, like other objects, are specific to Sites. There are no
permissions that cross over sites. All objects are readable regardless
of permissions. There is currently only one type of permissions a User
can have in order to make modifications:

    * admin
        - Ability to Update/Delete Site
        - Ability to grant permissions within a site
        - All subsequent permissions

Site creation is open to all users. Upon creating a Site you become
an admin of that Site with full permissions.

