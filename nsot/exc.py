from tornado.web import HTTPError

class Error(Exception):
    """ Baseclass for NSoT Exceptions."""

class ModelError(Error):
    """ Baseclass for NSoT Model Exceptions."""

class ValidationError(ModelError):
    """ Raised when validation fails on a model."""

class BaseHttpError(HTTPError):
    def __init__(self, log_message, *args, **kwargs):
        HTTPError.__init__(
            self, self.status_code, log_message, *args, **kwargs
        )

class BadRequest(BaseHttpError): status_code = 400
class Unauthorized(BaseHttpError): status_code = 401
class Forbidden(BaseHttpError): status_code = 403
class NotFound(BaseHttpError): status_code = 404
class Conflict(BaseHttpError): status_code = 409
