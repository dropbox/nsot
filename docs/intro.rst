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


Attributes
------------------

Attributes are arbitrary key/value pairs that can be assigned to
various resources. If an attribute is required then additions/updates
for that resource will require that attribute be present. Existing
resources will not be forcefully validated until update.

Permissions
-----------

Permissions, like other resources, are specific to Sites. There are no
permissions that cross over sites. All resources are readable regardless
of permissions. There are currently three types of permissions a User
can have in order to make modifications:

    * admin
        - Ability to Update/Delete Site
        - Ability to grant permissions within a site
        - All subsequent permissions
    * networks
        - Ability to Add/Update/Delete Networks
        - Ability to Add/Update/Delete Attributes for Networks.

Site creation is open to all users. Upon creating a Site you become
an admin of that Site with full permissions.

Changes
-------

All Create/Update/Delete events are logged as a Change. A Change includes
information such as the change time, user, and the full resource after
modification. Changes are immutable and can only be removed by deleting
the entire Site.
