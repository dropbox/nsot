# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.backends.sqlite3.base import DatabaseWrapper
from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.datastructures import DictWrapper
from django_extensions.db.fields.json import JSONField
from macaddress.fields import MACAddressField as BaseMACAddressField
import ipaddress
import logging
from smart_selects.db_fields import ChainedForeignKey
import types

from . import exc


__all__ = (
    'BinaryIPAddressField', 'ChainedForeignKey', 'JSONField', 'MACAddressField'
)


log = logging.getLogger(__name__)


if not hasattr(DatabaseWrapper, 'get_new_connection_is_patched'):
    """
    Monkey-patch SQLite3 driver to handle text as bytes.

    Credit: http://stackoverflow.com/a/28794677/194311
    """
    _get_new_connection = DatabaseWrapper.get_new_connection

    def _get_new_connection_tolerant(self, conn_params):
        conn = _get_new_connection(self, conn_params)
        conn.text_factory = bytes
        return conn

    DatabaseWrapper.get_new_connection = types.MethodType(
        _get_new_connection_tolerant, None, DatabaseWrapper
    )
    DatabaseWrapper.get_new_connection_is_patched = True


class BinaryIPAddressField(models.Field):
    """IP Address field that stores values as varbinary."""
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(BinaryIPAddressField, self).__init__(*args, **kwargs)
        self.editable = True

    def db_type(self, connection):
        data = DictWrapper(self.__dict__, connection.ops.quote_name, "qn_")
        return 'varbinary(%(max_length)s)' % data

    def to_python(self, value):
        """DB -> Python."""
        if not value:
            return value

        try:
            return ipaddress.ip_address(value).exploded
        except ValueError:
            return ipaddress.ip_address(bytes(value)).exploded

    def get_db_prep_value(self, value, connection, prepared=False):
        """Python -> DB."""
        return ipaddress.ip_address(value).packed


class MACAddressField(BaseMACAddressField):
    """
    Subclass of base field to raise a DRF ValidationError.

    DRF handles Django's default ValidationError, but this is so that we can
    always expect the DRF version, for better consistency in debugging and
    testing.
    """
    def to_python(self, value):
        try:
            return super(MACAddressField, self).to_python(value)
        except DjangoValidationError as err:
            raise exc.ValidationError(err.message)
