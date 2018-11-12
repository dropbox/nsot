##########
Data Model
##########

The Network Source of Truth is composed of various object types with which it is
important to be familiarized. This document describes each object type.

Sites
=====

Sites function as unique namespaces that can contain all other objects. Sites
allow an organization to have multiple instances of potentially conflicting
objects. For example, this could be beneficial for isolating corporate vs.
production environments, or pulling in the IP space of an acquisition.

Every object must be related to a site and therefore the ``site_id`` field is
used frequently to scope object lookups.

A Site cannot be deleted unless it contains no other objects.

A typical Site object might look like this:

.. code-block:: javascript

    {
        "id": 1,
        "name": "Demo Site",
        "description": "This is a demonstration site for NSoT."
    }

Attributes
==========

Attributes are arbitrary key/value pairs that can be assigned to various
resources. Attributes have various flags and constraints to control how they
may be used.

Attributes are bound to a *resource name* (e.g. Device). You may have multiple
Attributes with the same name bound to different resource types.

When assigned to objects, think of an Attribute as an instance of of an
Attribute object with a Value object assigned to it. Objects may be looked up
by their attribute/value pairs using set queries.

Attribute/value pairs are cached locally on on the containing object on write
to improve read performance.

A typical Attribute object might look like this:

.. code-block:: javascript

    {
        "multi": false,
        "resource_name": "Device",
        "description": "The device manufacturer.",
        "display": true,
        "required": true,
        "site_id": 1,
        "id": 2,
        "constraints": {
            "pattern": "",
            "valid_values": [
                "arista",
                "cisco",
                "juniper"
            ],
            "allow_empty": false
        },
        "name": "vendor"
    }

.. important::
    Changes to attribute flags and constraints are not retroactive. Existing
    resources will not be forcefully validated until updated.

Values
------

Values contain atttribute values. These are never directly manipulated, but
they are accessible from the API for utilty.

All attribute values must be strings. If an attribute is a list type
(``multi=True``), then the values for that attribute will be a list of strings.

A typical Value object might look like:

.. code-block:: javascript

    {
        "id": 8,
        "name": "owner",
        "value": "jathan",
        "attribute": 5,
        "resource_name": "Device",
        "resource_id": 2
    }

Flags
-----

required
    If an attribute is required then additions/updates for that resource will
    require that attribute be present.

display
    Whether to display the attribute in the web UI. Required attributes are
    always displayed.

multi
    Whether the attribute values should be treated as a list type

Constraints
-----------

pattern
    A regex pattern. If set, values for this attribute must match the pattern.

allow_empty
    Whether the attribute should require a value. This causes the attribute to
    behave like a tag.

valid_values
    Valid values for this attribute. This causes the attribute to behave like
    an enum.

.. _set-queries:

Set Queries
-----------

All Resource types support set query operations. Set queries are a powerful
part of the data model that allow you to perform complex lookups of objects by
attribute/value pairs.

Set queries can be performed using a simple string-based syntax.

The operations are evaluated from left-to-right, where the first character
indicates the set operation:

+ ``+`` indicates a set *union*
+ ``-`` indicates a set *difference*
+ no marker indicates a set *intersection*

For example, when using set queries to lookup Device objects:

+ ``"vendor=juniper"`` would return the set intersection of objects with
  ``vendor=juniper``.
+ ``"vendor=juniper -metro=iad"`` would return the set difference of all
  objects with ``vendor=juniper`` (that is all ``vendor=juniper`` where
  ``metro`` is not ``iad``).
+ ``"vendor=juniper +vendor=cisco`` would return the set union of all
  objects with ``vendor=juniper`` or ``vendor=cisco`` (that is all objects
  matching either).

The ordering of these operations is important. If you are not familiar with set
operations, please check out `Basic set theory concepts and notation
<http://en.wikipedia.org/wiki/Set_theory#Basic_concepts_and_notation>`_
(Wikipedia).

For how set queries can be performed, please see the REST API
documentation on :ref:`api-set-queries`.

.. _resources:

Resources
=========

A Resource object is any object that can have attributes. The primary resource
types are:

.. contents::
    :local:
    :depth: 1

Devices
-------

A Device represents various hardware components on your network such as
routers, switches, console servers, pdus, servers, etc.

Devices in their most basic form are represented by a hostname.

Devices can contain zero or more Interfaces.

A typical Device object might look like:

.. code-block:: javascript

    {
        "attributes": {
            "owner": "jathan",
            "vendor": "juniper",
            "hw_type": "router",
            "metro": "lax"
        },
        "hostname": "lax-r1",
        "site_id": 1,
        "id": 1
    }

Networks
--------

Networks in NSoT are designed to provide IP Address Management (IPAM)
features. A Network represents an IPv4 or IPv6 Network or IP address. Working with
networks is usually done with CIDR notation.

Networks may be assigned to Interfaces by way of an *Assignment* relationship.

A typical Network object might look like:

.. code-block:: javascript

    {
        "parent_id": null,
        "parent": null,
        "state": "allocated",
        "prefix_length": 8,
        "is_ip": false,
        "ip_version": "4",
        "network_address": "10.0.0.0",
        "cidr": "10.0.0.0/8",
        "attributes": {
            "type": "internal"
        },
        "site_id": 1,
        "id": 1
    }

Tree Traversal
~~~~~~~~~~~~~~

Networks are represented as tree objects. Anytime a network is added or
deleted, the tree is automatically updated to reparent networks appropriately.

Networks support all of the common tree traversal methods that you may expect
from this type of object:

parent
    The parent of this network

ancestors
    All parents of the parent of this network

siblings
    Networks with the same parent as this network

children
    The child networks of this network

descendents
    .. deprecated:: 1.1
    Use *descendants* instead, which is the correctly spelled version of the
    same method.

descendants
    All children of the children of this network

closest_parent
    If this network doesn't exist, who might its parent be if it did?

subnets
    Subnetworks of this network

supernets
    Supernets of this network

State
~~~~~

Network state represents whether the Network is in use or not. The states are:

allocated
    The default state for any newly-created Network. It is implied that this
    address is in use some how, but it is not a busy state.

assigned
    Used to represent a Network assigned to an Interface. This is a busy state.

reserved
    Used to represent that the Network is reserved for future use. This is a
    busy state.

orphaned
    Used to represent a Network that was previously assigned or reserved but
    has since drifted.

Allocation
~~~~~~~~~~

Networks can be used to allocate child networks or addresses.

next_network
    Given a prefix_length, return the next available child Network of this
    length.

next_address
    Given a number of addresses, return that many next available IP addresses.

Interfaces
----------

An Interface represents a physical or logical network interface such as an
ethernet port. Interfaces must always be associated with a device. Zero or
more addresses may be assigned to an Interface, although the same address may
not be assigned to more than one interface on the same device.

A typical Interface object might look like:

.. code-block:: javascript

    {
        "addresses": [
            "10.10.10.1/32"
        ],
        "device": 1,
        "device_hostname": "lax-r1",
        "speed": 10000,
        "networks": [
            "10.10.10.0/24"
        ],
        "description": "this is ae0.0",
        "name": "ae0.0",
        "name_slug": "lax-r1:ae0.0",
        "id": 2,
        "parent_id": 1,
        "parent": "lax-r1:ae0",
        "mac_address": null,
        "attributes": {
            "vlan": "100"
        },
        "type": 6
    }

Addresses
~~~~~~~~~

An address assignment to an Interface is represented by an *Assignment*
relationship to a Network object.

If a Network object for the desired IP address assignment does not exist at the
time of assignment, one is created and set to the state ``assigned``.

If a Network object already exists and is not in a "busy state", then it will
be assigned to the Interface.

Assignments
~~~~~~~~~~~

Assignments represent the relationship and constraints for a Network to be
associated to an Interface.

The following constraints are enforced:

* An address may not be assigned to a to more than one Interface on any given
  Device.
* Only a Network containing a host address with a prefix of ``/32`` (IPv4) or
  ``/128`` (IPv6) may be assigned to an Interface.

Networks
~~~~~~~~

The networks for an Interface are the are read-only representation of the
derived parent Network objects of any addresses assigned to an Interface.

Circuits
--------

A Circuit represents a physical or logical circuit between two network
interfaces, such as a backbone interconnect or external peering.

Circuits are created by binding local (A-side) and remote (Z-side) Interface
objects. Interfaces may only be bound to a single Circuit at a time. The Z-side
Interface is optional, such as if you want to model a circuit for which you do
not own the remote side.

The Circuit name defaults to the natural key (slug) representations of the A
and Z interfaces, but may also be customized.

A Circuit's "name slug" may sometimes differ from its name due to certain
special characters that complicate API lookups. The name slug is used to
uniquely identify the Circuit internally.

A typical Circuit object might look like:

.. code-block:: javascript

    {
        "name": "lax-r1:ae0_jfk-r1:ae0",
        "endpoint_a": "lax-r1:ae0",
        "endpoint_z": "jfk-r1:ae0",
        "name_slug": "lax-r1:ae0_jfk-r1:ae0",
        "attributes": {},
        "id": 1
    }

Addresses
~~~~~~~~~

Returns the addresses assigned to the member Interfaces of the Circuit, as well as the addresses
assigned to the child Interfaces of the Circuit, if any.

Devices
~~~~~~~

Returns the Devices to which the member Interfaces are attached.

Interfaces
~~~~~~~~~~

Returns the Interface objects bound to the circuit ordered from A to Z (local
to remote).

ProtocolTypes
-------------

A ProtocolType represent the type for a Protocol and is a required value for
the ``Protocol.type`` field when a Protocol is created. 

ProtocolTypes are created by specifying the unique name, a user-friendly
description, and required Protocol attributes for Protocols of this type.

This object is designed to provide flexibility in customizing the modeling of
protocol sessions for any environment by utilizing varying sets of Protocol
attributes.

For example one could create "iBGP" and "eBGP" ProtocolTypes with different
sets of required Protocol attributes that could be utilized for internal and
external BGP sessions.

A ProtocolType's "name" field must be unique for a given Site. Any Protocol
attributes you wish to set as required attributes must exist prior to creating
the ProtocolType.

A typical ProtocolType object might look like:

.. code-block:: javascript

    {
        "site": 1,
        "description": "IS-IS",
        "id": 1,
        "required_attributes": [
            "metric"
        ],
        "name": "isis"
    }


Protocols
---------

A Protocol represents a session for a network protocol such as BGP, IS-IS, or OSPF. 

Before a Protocol can be created, a ProtocolType with the desired name and
required attributes must first be created. A Protocol must be bound to a Device
object and a ProtocolType.

A Protocol may optionally be bound to an Interface or a Circuit, but not both.

A typical Protocol object might look like:

.. code-block:: javascript

   {
        "interface": "foo-bar1:ae0",
        "description": "IS-IS link for ae0",
        "circuit": null,
        "attributes": {},
        "device": "foo-bar1",
        "auth_string": "abc123",
        "type": "isis",
        "id": 1,
        "site": 1
    }

Changes
=======

All Create/Update/Delete events are logged as a Change. A Change includes
information such as the change time, user, and the full object payload after
modification.

Changes are immutable and can only be removed by deleting the entire Site.

A typical Change object might look like:

.. code-block:: javascript

    {
        "event": "Create",
        "change_at": 1460994054,
        "resource_name": "Attribute",
        "resource": {
            "multi": false,
            "resource_name": "Interface",
            "description": "",
            "required": false,
            "site_id": 1,
            "display": false,
            "constraints": {
                "pattern": "",
                "valid_values": [],
                "allow_empty": false
            },
            "id": 9,
            "name": "foo"
        },
        "user": {
            "id": 1,
            "email": "admin@localhost"
        },
        "resource_id": 9,
        "id": 36,
        "site": {
            "description": "This is a demonstration site for NSoT.",
            "id": 1,
            "name": "Demo Site"
        }
    }

Users
=====

Users are for logging into stuff. Users in NSoT are represented by an email
address.

Users have a "secret key" that can be used for API authentication.

A typical User might look like:

.. code-block:: javascript

    {
        "id": 1,
        "email": "admin@localhost",
        "permissions": {
            "1": {
                "user_id": 1,
                "site_id": 1,
                "permissions": [
                    "admin"
                ]
            }
        }
    }

Permissions
===========

By default all new users have superuser (admin) and therefore modifying
permissions is not necessary in default installations.

Permissions control three basic actions for each object and come in two
flavors: global and object-level.

The basic permissions for each object are:

* add
* change
* delete

Global Permissions
------------------

If assigning permissions to a user or a group, global permissions can be
assigned to individual resource type, for example "Add Network" or "Change
Device".

Object-level Permissions
------------------------

Permissions can also be assigned to individual objects, for example
``Network('10.10.10.0/24')``. These permissions can be added from the admin
dashboard view for the object.

For tree objects (currently ``Interface`` and ``Network`` objects) that can
have children and ancestors, the permissions will be inherited by child nodes
*unless a more specific permission has been set on the child object*.
