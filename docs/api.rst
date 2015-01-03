API Documentation
*****************

NSoT is designed as an API first so anything possible in the Web UI
or command line tools would be available here.

Authentication
--------------

In normal operation NSoT is expected to be run behind an authenticating
proxy that passes back a specific header. By default we expect
``X-NSoT-Email``, though it is configurable.

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
