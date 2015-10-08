Introduction
============

The Network Source of Truth is composed of various resources that it's
important to be familiar with. This page will describe the various
resources.

Sites
-----

Sites function as unique namespaces that can contain other resources.
Sites allow an organization to have multiple instances of potentially
conflicting resources. This could be beneficial for isolating corp vs.
prod environments, or pulling in the IP space of an aquisition.

Attributes
----------

Attributes are arbitrary key/value pairs that can be assigned to
various resources. If an attribute is required then additions/updates
for that resource will require that attribute be present.

Changes to attribute constraints are not retroactive. Existing
resources will not be forcefully validated until updated.

Networks
--------

A network resource can represent an IP Network and an IP Address. Working
with networks is usually done with CIDR notation.

Networks can have any number of arbitrary attributes as defined below.

Devices
-------

A device represents various hardware components on your network such as
routers, switches, console servers, pdus, servers, etc.

Devices also support arbitrary attributes similar to Networks.

Interfaces
----------

An interface represents a physical or logical network interface such as an
ethernet port. Interfaces must always be associated with a device. Zero or
more addresses may be assigned to an Interface, although the same address may
not be assigned to more than one interface on the same device.

Interfaces also support arbitrary attributes similar to Networks and Devices.

Permissions
-----------

Permissions, like other resources, are specific to Sites. There are no
permissions that cross over sites. All resources are readable regardless
of permissions. There is currently only one type of permissions a User
can have in order to make modifications:

    * admin
        - Ability to Update/Delete Site
        - Ability to grant permissions within a site
        - All subsequent permissions

Site creation is open to all users. Upon creating a Site you become
an admin of that Site with full permissions.

Changes
-------

All Create/Update/Delete events are logged as a Change. A Change includes
information such as the change time, user, and the full resource after
modification. Changes are immutable and can only be removed by deleting
the entire Site.
