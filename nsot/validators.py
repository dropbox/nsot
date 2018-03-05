"""
Validators for validating object fields.
"""

from django.conf import settings
from django.core.validators import EmailValidator
import ipaddress
import netaddr

from . import exc


def validate_mac_address(value):
    """Validate whether ``value`` is a valid MAC address."""
    if value is None:
        return value

    # If the incoming value is a string, cast it to an int
    if isinstance(value, basestring) and value.isdigit():
        value = int(value)

    # Directly invoke EUI object instead of using MACAddressField
    try:
        value = netaddr.EUI(value, version=48)
    except (ValueError, TypeError, netaddr.AddrFormatError):
        raise exc.ValidationError({
            'mac_address': 'Enter a valid MAC Address.'
        })

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
    """Validate whether ``value`` is a host IP address."""
    cidr = validate_cidr(value)
    if cidr.prefixlen not in settings.HOST_PREFIXES:
        raise exc.ValidationError({
            'address': '%r is not a valid host address!' % value
        })
    return value


def validate_email(value):
    """Validate whether ``value`` is an email address."""
    validator = EmailValidator()
    try:
        validator(value)
    except exc.DjangoValidationError as err:
        raise exc.ValidationError({
            'email': err.message
        })
    return value
