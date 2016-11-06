########
REST API
########

NSoT is designed as an API-first application so that all possible actions are
published as API endpoints.

.. _api-ref:

API Reference
=============

Interactive API reference documentation can be found by browsing to ``/docs/``
on a running NSoT server instance.

.. _browsable-api:

Browsable API
=============

Because NSoT is an API-first application, the REST API is central to the
experience. The REST API can support JSON or can also be used directly from
your web browser. This version is called the "browsable API" and while it
doesn't facilitate automation, it can be very useful.

Visit ``/api/`` in your browser on your installed instance. How cool is that?!

.. _api-auth:

Authentication
==============

Two methods of authentication are currently supported.

.. _api-auth_header:

User Authentication Header
--------------------------

This is referred to internally as **auth_header** authentication.

In normal operation NSoT is expected to be run behind an authenticating proxy
that passes back a specific header. By default we expect ``X-NSoT-Email``,
though it is configurable using the ``USER_AUTH_HEADER`` setting.

The value of this header must be the user's ``email`` and is formatted like
so:

.. code-block:: javascript

    X-NSoT-Email: {email}

.. _api-auth_token:

AuthToken
---------

This is referred to internally as **auth_token** authentication.

API authentication requires the ``email`` and ``secret_key``
of a user. When a user is first created, a ``secret_key`` is automatically
generated. The user may obtain their ``secret_key`` from the web interface.

Users make a POST request to ``/api/authenticate/`` to passing ``email`` and
``secret_key`` in ``JSON`` payload. They are returned an ``auth_token`` that can
then be used to make API calls. The ``auth_token`` is short-lived (default is
10 minutes and can be change using the ``AUTH_TOKEN_EXPIRY`` setting). Once the
token expires a new one must be obtained.

The ``auth_token`` must be sent to the API using an ``Authorization`` header
that is formatted like so:

.. code-block:: javascript

    Authorization: AuthToken {email}:{secret_key}

Requests
========

In addition to the authentication header above all ``POST``, ``PUT``, and
``PATCH``, requests will be sent as ``JSON`` rather than form data and should
include the header ``Content-Type: application/json``

``PUT`` requests are of note as they are expected to set the state of all
mutable fields on a resource. This means if you don't specificy all optional
fields may revert to their default values, depending on the object type.

``PATCH`` allows for partial update of objects for most fields, depending on
the object type.

``OPTIONS`` will provide the schema for any endpoint.

Responses
=========

All responses will be in format along with the header ``Content-Type:
application/json`` set.

The ``JSON`` payload will be in one of two potential structures and will always
contain a ``status`` field to distinguish between them. If the ``status`` field
has a value of ``"ok"``, then the request was successful and the response will
be available in the ``data`` field.

.. code-block:: javascript

    {
        ...
    }

If the ``status`` field has a value of ``"error"`` then the response failed
in some way. You will have access to the error from the ``error`` field which
will contain an error ``code`` and ``message``.

.. code-block:: javascript

    {
        "error": {
            "code": 404,
            "message": "Resource not found."
        }
    }

Pagination
==========

All responses that return a list of resources will support pagination. If the
``results`` object on the response has a ``count`` attribute then the endpoint
supports pagination. When making a request against this endpoint ``limit`` and
``offset`` query parameters are supported.

The response will also include ``next`` and ``previous`` URLs that can be used
to retrieve the next set of results. If there are not any more results
available, their value will be ``null``.

An example response for querying the ``sites`` endpoint might look like:

**Request**:

.. code-block:: http

    GET http://localhost:8990/api/sites/?limit=1&offset=0

**Response**:

.. code-block:: javascript

    {
        "count": 1,
        "next": "http://localhost:8990/api/sites/?limit=1&offset=1",
        "previous": null,
        "results": [
            {
                "id": 1
                "name": "Site 1",
                "description": ""
            }
        ]
    }

Schemas
=======

By performing an ``OPTIONS`` query on any endpoint, you can obtain the schema
of the resource for that endpoint. This includes supported content-types, HTTP
actions, the fields allowed for each action, and their attributes.

An example response for the schema for the ``devices`` endpoint might look like:

**Request**:

.. code-block:: http

    OPTIONS http://localhost:8990/api/devices/

**Response**:

.. code-block:: javascript

    HTTP 200 OK
    Allow: GET, POST, PUT, PATCH, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    {
        "name": "Device List",
        "description": "API endpoint that allows Devices to be viewed or edited.",
        "renders": [
            "application/json",
            "text/html"
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ],
        "actions": {
            "PUT": {
                "id": {
                    "type": "integer",
                    "required": false,
                    "read_only": true,
                    "label": "ID"
                },
                "hostname": {
                    "type": "string",
                    "required": true,
                    "read_only": false,
                    "label": "Hostname",
                    "max_length": 255
                },
                "attributes": {
                    "type": "field",
                    "required": true,
                    "read_only": false,
                    "label": "Attributes",
                    "help_text": "Dictionary of attributes to set."
                }
            },
            "POST": {
                "hostname": {
                    "type": "string",
                    "required": true,
                    "read_only": false,
                    "label": "Hostname",
                    "max_length": 255
                },
                "attributes": {
                    "type": "field",
                    "required": false,
                    "read_only": false,
                    "label": "Attributes",
                    "help_text": "Dictionary of attributes to set."
                },
                "site_id": {
                    "type": "integer",
                    "required": true,
                    "read_only": false,
                    "label": "Site id"
                }
            }
        }
    }

.. _api-set-queries:

Performing Set Queries
======================

:ref:`set-queries` allow you to perform complex lookups of objects by
attribute/value pairs and are available on all :ref:`resources` at the
``/api/:resource/query/`` list endpoint for a given resource type.

To perform a set query you must perform a ``GET`` request to the query endpoint
providing the set query string as a value to the ``query`` argument.

For example:

**Request**:

.. code-block:: http

   GET /api/devices/query/?query=vendor=juniper

**Response**:

.. code-block:: javascript

    HTTP 200 OK
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    [
        {
            "attributes": {
                "owner": "jathan",
                "vendor": "juniper",
                "hw_type": "router",
                "metro": "lax"
            },
            "hostname": "lax-r2",
            "site_id": 1,
            "id": 2
        },
        {
            "attributes": {
                "owner": "jathan",
                "vendor": "juniper",
                "hw_type": "router",
                "metro": "iad"
            },
            "hostname": "iad-r1",
            "site_id": 1,
            "id": 5
        }
    ]

The optional ``unique`` argument can also be provided in order to ensure only
a single object is returned, otherwise an error is returned.

**Request**:

.. code-block:: http

   GET /api/devices/query/?query=metro=iad&unique=true

**Response**:

.. code-block:: javascript

    HTTP 200 OK
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    [
        {
            "attributes": {
                "owner": "jathan",
                "vendor": "juniper",
                "hw_type": "router",
                "metro": "iad"
            },
            "hostname": "iad-r1",
            "site_id": 1,
            "id": 5
        }
    ]

If multiple results match the query, when ``unique`` has been specified,
an error will be returned.

**Request**:

.. code-block:: http

   GET /api/devices/query/?query=vendor=juniper

**Response**:

.. code-block:: javascript

    HTTP 400 Bad Request
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/json
    Vary: Accept

    {
        "error": {
            "message": {
                "query": "Query returned 2 results, but exactly 1 expected"
            },
            "code": 400
        }
    }

Resthooks
=========

NSoT implements resthooks_ for subscribing to adds, changes, and removals of
resource types. To do this, the hook needs to be created with a valid event
name and target to receive the update

.. _resthooks: http://resthooks.org/

Event names are in the format of ``resource_name.action``. Current valid
actions are:

* ``added``
* ``changed``
* ``removed``

Creating a hook:

.. code-block:: http

    POST /api/hooks/

.. code-block:: javascript

    {
        "event": "network.added",
        "target": "http://netwatcher.company.com"
    }

Checking details of a hook:

.. code-block:: http

    GET /api/hooks/:id

.. code-block:: javascript

    {
        "id": 2,
        "created": "2016-11-06T01:15:32.259000",
        "updated": "2016-11-06T01:16:50.925442",
        "event": "network.added",
        "target": "http://localhost:8888",
        "user": 1
    }

Payload target server can expect to receive:

.. code-block:: http

    POST /

.. code-block:: javascript

    {
        "hook": {
            "target": "http://localhost:8888",
            "id": 2,
            "event": "network.added"
        },
        "data": {
            "parent_id": 6,
            "state": "allocated",
            "prefix_length": 16,
            "is_ip": false,
            "ip_version": "4",
            "network_address": "192.168.0.0",
            "attributes": {},
            "site_id": 1,
            "id": 7
        }
    }

Things to note
--------------

* Pushes will not retry currently
