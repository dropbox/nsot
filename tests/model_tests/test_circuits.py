# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
import ipaddress
import logging

from nsot import exc, models

from .fixtures import admin_user, circuit, device, site, user, transactional_db


def test_creation(device):
    """Test basic Circuit creation."""
    site = device.site

    # Create a network for interface assignments
    network = models.Network.objects.create(
        cidr='10.32.0.0/24', site=site,
    )

    # A-side device/interface
    device_a = device
    iface_a = models.Interface.objects.create(
        device=device_a, name='eth0/1', addresses=['10.32.0.1/32']
    )

    # Z-side device/interface
    device_z = models.Device.objects.create(
        hostname='foo-bar2', site=site
    )
    iface_z = models.Interface.objects.create(
        device=device_z, name='eth0/1', addresses=['10.32.0.2/32']
    )

    # Create the circuit
    circuit = models.Circuit.objects.create(
        endpoint_a=iface_a, endpoint_z=iface_z
    )

    # Interface inherits endpoint_a's site
    assert circuit.site == iface_a.site

    # Name should be slugs of A/Z interfaces joined by '_'
    expected_name_t = '{endpoint_a}_{endpoint_z}'
    expected_name = expected_name_t.format(
        endpoint_a=iface_a, endpoint_z=iface_z
    )
    assert circuit.name == expected_name

    # Name slug should be the slugified version of the name
    assert circuit.name_slug == expected_name.replace('/', '_')

    # Assert property values
    assert circuit.interfaces == [iface_a, iface_z]
    assert [str(a) for a in circuit.addresses] == ['10.32.0.1/32', '10.32.0.2/32']
    assert circuit.devices == [device_a, device_z]

    # Try to create another circuit w/ the same interfaces (expecting Django
    # validation error)
    with pytest.raises(DjangoValidationError):
        c2 = models.Circuit.objects.create(
            endpoint_a=iface_a, endpoint_z=iface_z
        )

    # ... Or with A/Z sides swapped (expecting DRF validation error).
    with pytest.raises(exc.ValidationError):
        c2 = models.Circuit.objects.create(
            endpoint_a=iface_z, endpoint_z=iface_a
        )


def test_attributes(circuit):
    """Test that attributes work as expected."""
    models.Attribute.objects.create(
        site=circuit.site, resource_name='Circuit', name='cid'
    )
    models.Attribute.objects.create(
        site=circuit.site, resource_name='Circuit', name='vendor'
    )

    # Set attributes
    attrs = {'cid': 'abc123', 'vendor': 'acme'}
    circuit.set_attributes(attrs)
    assert circuit.get_attributes() == attrs

    # Test a sinmple set query just for kicks.
    query_result = models.Circuit.objects.set_query('cid=abc123 vendor=acme')
    assert list(query_result) == [circuit]

    # Verify that we can zero out attributes
    circuit.set_attributes({})
    assert circuit.get_attributes() == {}

    # And make sure no bogus attributes can be set.
    with pytest.raises(exc.ValidationError):
        circuit.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        circuit.set_attributes({0: 'value'})

    with pytest.raises(exc.ValidationError):
        circuit.set_attributes({'key': 0})

    with pytest.raises(exc.ValidationError):
        circuit.set_attributes({'made_up': 'value'})
