from __future__ import unicode_literals
from __future__ import absolute_import
from collections import OrderedDict
import logging

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.db import IntegrityError
from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


log = logging.getLogger(__name__)


__all__ = (
    "Error",
    "ModelError",
    "BaseHttpError",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "DjangoValidationError",
    "ObjectDoesNotExist",
    "ProtectedError",
    "ValidationError",
    "MultipleObjectsReturned",
)


def custom_exception_handler(exc, context):
    """Always handle errors all pretty-like."""
    # Call REST framework's default exception handler first to get the standard
    # error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code and message to the response.
    # We want an error response to look like this:
    # {
    #     "error": {
    #         "message": "Endpoint not found",
    #         "code": 404
    #     }
    # }
    log.debug("custom_exception_handler: exc = %r", exc)
    log.debug("custom_exception_handler: context = %r", context)
    if response is not None:
        orig_data = response.data
        log.debug("custom_exception_handler: orig_data = %r", orig_data)

        try:
            message = orig_data["detail"]
            if message == "Not found.":
                message = "Endpoint not found."
        except KeyError:
            message = orig_data
        except TypeError:
            message = orig_data[0]

        data = OrderedDict(
            [
                (
                    "error",
                    {
                        "message": message,
                        "code": response.status_code,
                    },
                ),
            ]
        )
        response.data = data

    request = context["request"]
    log.debug("custom_exception_handler: request = %r", request)
    log.debug("custom_exception_handler: dir(request) = %r", dir(request))
    log.debug("custom_exception_handler: request.data = %r", request.data)

    return response


class Error(APIException):
    """ Baseclass for NSoT Exceptions."""


class ModelError(Error):
    """Base class for NSoT Model Exceptions."""


class BaseHttpError(Error):
    """Base HTTP error."""

    pass


class BadRequest(BaseHttpError):
    """HTTP 400 error."""

    status_code = 400


class Unauthorized(BaseHttpError):
    """HTTP 401 error."""

    status_code = 401


class Forbidden(BaseHttpError):
    """HTTP 403 error."""

    status_code = 403


class NotFound(BaseHttpError):
    """HTTP 404 error."""

    status_code = 404
    default_detail = "Endpoint not found."


class Conflict(BaseHttpError, IntegrityError):
    """HTTP 409 error."""

    status_code = 409
