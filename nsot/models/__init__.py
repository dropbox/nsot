# -*- coding: utf-8 -*-
from django.db import models as djmodels

from .assignment import Assignment
from .attribute import Attribute
from .change import Change
from .circuit import Circuit
from .device import Device
from .interface import Interface
from .network import Network
from .protocol import Protocol
from .protocol_type import ProtocolType
from .resource import Resource
from .site import Site
from .user import User
from .value import Value


__all__ = [
    'Assignment',
    'Attribute',
    'Change',
    'Circuit',
    'Device',
    'Interface',
    'Network',
    'Protocol',
    'ProtocolType',
    'Site',
    'User',
    'Value',
]


# Global signals
def delete_resource_values(sender, instance, **kwargs):
    """Delete values when a Resource object is deleted."""
    instance.attributes.delete()  # These are instances of Value


resource_subclasses = Resource.__subclasses__()
for model_class in resource_subclasses:
    # Value post_delete
    djmodels.signals.post_delete.connect(
        delete_resource_values,
        sender=model_class,
        dispatch_uid='value_post_delete_' + model_class.__name__
    )
