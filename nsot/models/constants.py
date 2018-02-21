from django.conf import settings

# These are constants that becuase they are tied directly to the underlying
# objects are explicitly NOT USER CONFIGURABLE.
RESOURCE_BY_IDX = (
    'Site', 'Network', 'Attribute', 'Device', 'Interface', 'Circuit',
    'Protocol', 'ProtocolType'
)
RESOURCE_BY_NAME = {
    obj_type: idx
    for idx, obj_type in enumerate(RESOURCE_BY_IDX)
}

CHANGE_EVENTS = ('Create', 'Update', 'Delete')

VALID_CHANGE_RESOURCES = set(RESOURCE_BY_IDX)
VALID_ATTRIBUTE_RESOURCES = set([
    'Network', 'Device', 'Interface', 'Circuit', 'Protocol'
])

# Lists of 2-tuples of (value, option) for displaying choices in certain model
# serializer/form fields.
CHANGE_RESOURCE_CHOICES = [(c, c) for c in VALID_CHANGE_RESOURCES]
EVENT_CHOICES = [(c, c) for c in CHANGE_EVENTS]
IP_VERSION_CHOICES = [(c, c) for c in settings.IP_VERSIONS]
RESOURCE_CHOICES = [(c, c) for c in VALID_ATTRIBUTE_RESOURCES]

# Unique interface type IDs.
INTERFACE_TYPES = [t[0] for t in settings.INTERFACE_TYPE_CHOICES]
