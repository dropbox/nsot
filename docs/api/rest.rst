REST API
========

NSoT is designed as an API-first application so that all possible actions are
published as API endpoints.

.. _api-ref:

API Reference
-------------

Interactive API reference documentation can be found by browsing to ``/docs/``
on a running NSoT server instance.

.. _api-auth:

Authentication
--------------

Two methods of authentication are currently supported.

.. _api-auth_header:

User Authentication Header
~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~

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
--------

In addition to the authentication header above all ``POST``, ``PUT``, and
``PATCH``, requests will be sent as ``JSON`` rather than form data and should
include the header ``Content-Type: application/json``

``PUT`` requests are of note as they are expected to set the state of all
mutable fields on a resource. This means if you don't specificy all optional
fields may revert to their default values, depending on the object type.

``PATCH`` allows for partial update of objects for most fields, depending on
the object type.

Responses
---------
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
----------

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

