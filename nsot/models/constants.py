"""
Constants for working with models.
"""

from __future__ import absolute_import
from collections import OrderedDict

from django.conf import settings


# These are constants that becuase they are tied directly to the underlying
# objects are explicitly NOT USER CONFIGURABLE.
RESOURCE_BY_IDX = (
    "Site",
    "Network",
    "Attribute",
    "Device",
    "Interface",
    "Circuit",
    "Protocol",
    "ProtocolType",
)
RESOURCE_BY_NAME = OrderedDict(
    (obj_type, idx) for idx, obj_type in enumerate(RESOURCE_BY_IDX)
)

# Valid change event types
CHANGE_EVENTS = ("Create", "Update", "Delete")

# Resource objects that can be used for Change events
VALID_CHANGE_RESOURCES = tuple(RESOURCE_BY_IDX)

# Resource objects that can have attributes
VALID_ATTRIBUTE_RESOURCES = (
    "Network",
    "Device",
    "Interface",
    "Circuit",
    "Protocol",
)

# Lists of 2-tuples of (value, option) for displaying choices in certain model
# serializer/form fields.
CHANGE_RESOURCE_CHOICES = [(c, c) for c in VALID_CHANGE_RESOURCES]
EVENT_CHOICES = [(c, c) for c in CHANGE_EVENTS]
IP_VERSION_CHOICES = [(c, c) for c in settings.IP_VERSIONS]
RESOURCE_CHOICES = [(c, c) for c in VALID_ATTRIBUTE_RESOURCES]

# Unique interface type IDs.
INTERFACE_TYPES = [t[0] for t in settings.INTERFACE_TYPE_CHOICES]
