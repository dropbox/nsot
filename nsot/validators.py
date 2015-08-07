"""
Validators for validating object fields.
"""

from django.conf import settings
import ipaddress
from macaddress.formfields import MACAddressField as MACAddressFormField

from . import exc


def validate_mac_address(value):
    """Validate whether ``value`` is a valid MAC address."""
    field = MACAddressFormField()
    field.clean(value)
    return value


def validate_name(value):
    """Validate whether ``value`` is a valid name."""
    if not value:
        raise exc.ValidationError({
            'name': 'This is a required field.'
        })
    return value


def validate_cidr(value):
    """Validate whether ``value`` is a validr IPv4/IPv6 CIDR."""
    try:
        cidr = ipaddress.ip_network(unicode(value))
    except ValueError:
        raise exc.ValidationError({
            'cidr': '%r does not appear to be an IPv4 or IPv6 network' % value
        })
    else:
        return cidr


def validate_host_address(value):
    cidr = validate_cidr(value)
    if cidr.prefixlen not in settings.HOST_PREFIXES:
        raise exc.ValidationError({
            'address': '%r is not a valid host address!' % value
        })
    return value
