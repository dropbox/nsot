API Documentation
*****************

NSoT is designed as an API first so anything possible in the Web UI
or command line tools would be available here.

Authentication
--------------

Two methods of authentication are currently supported.

User Authentication Header
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is referred to internally as **auth_header** authentication.

In normal operation NSoT is expected to be run behind an authenticating proxy
that passes back a specific header. By default we expect ``X-NSoT-Email``,
though it is configurable using the ``user_auth_header`` setting.

The value of this header must be the user's ``email`` and is formatted like so::

    X-NSoT-Email: {email}

AuthToken
~~~~~~~~~

This is referred to internally as **auth_token** authentication.

API authentication requires the ``email`` and ``secret_key``
of a user. When a user is first created, a ``secret_key`` is automatically
generated. The user may obtain their ``secret_key`` from the web interface.

Users make a POST request to ``/api/authenticate`` to passing ``email`` and
``secret_key`` in JSON payload. They are returned an ``auth_token`` that can
then be used to make API calls. The ``auth_token`` is short-lived (default is
10 minutes and can be change using the ``auth_token_expiry`` setting). Once the
token expires a new one must be obtained.

The ``auth_token`` must be sent to the API using an ``Authorization`` header
that is formatted like so::

    Authorization: AuthToken {email}:{secret_key}

Please see the :ref:`api-ref` for examples.

Requests
--------

In addition to the authentication header above all ``POST``/``PUT`` requests
will be sent as json rather than form data and should include the header ``Content-Type: application/json``

``PUT`` requests are of note as they are expected to set the state of all mutable fields on a resource. This means if you don't specificy all optional fields they will revert to their default values.

Responses
---------
All responses will be in ``JSON`` format along with the header
``Content-Type: application/json`` set.

The ``JSON`` payload will be in one of two potential structures and will always contain a ``status`` field to distinguish between them. If the ``status`` field
has a value of ``"ok"``, then the request was successful and the response will
be available in the ``data`` field.

.. sourcecode:: javascript

    {
        "status": "ok",
        "data": {
            ...
        }
    }

If the ``status`` field has a value of ``"error"`` then the response failed
in some way. You will have access to the error from the ``error`` field which
will contain an error ``code`` and ``message``.

.. sourcecode:: javascript

    {
        "status": "error",
        "error": {
            "code": 404,
            "message": "Resource not found."
        }
    }

Pagination
----------

Most, if not all, responses that return a list of resources will support pagination. If the
``data`` object on the response has a ``total`` attribute then the endpoint supports pagination.
When making a request against this endpoint ``limit`` and ``offset`` query parameters are
supported.

An example response for querying the ``sites`` endpoint might look like:

.. sourcecode:: javascript

    {
        "status": "ok",
        "data": {
            "sites": [
                {
                    "id": 1
                    "name": "Site 1",
                    "description": ""
                }
            ],
            "limit": null,
            "offset": 0,
            "total": 1
        }
    }

