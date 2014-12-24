class Error(Exception):
    """ Baseclass for NSoT Exceptions."""

class ModelError(Error):
    """ Baseclass for NSoT Model Exceptions."""

class ValidationError(ModelError):
    """ Raised when validation fails on a model."""
