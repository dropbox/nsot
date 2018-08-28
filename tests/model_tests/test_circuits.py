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

    # A-side device/interface and child interface
    device_a = device
    iface_a = models.Interface.objects.create(
        device=device_a, name='ae0', addresses=['10.32.0.1/32']
    )
    child_iface_a = models.Interface.objects.create(
        device=device_a, name='ae0.0', addresses=['10.32.0.3/32'], parent=iface_a
    )

    # Z-side device/interface and child interface
    device_z = models.Device.objects.create(
        hostname='foo-bar2', site=site
    )
    iface_z = models.Interface.objects.create(
        device=device_z, name='ae0', addresses=['10.32.0.2/32']
    )
    child_iface_z = models.Interface.objects.create(
        device=device_z, name='ae0.0', addresses=['10.32.0.4/32'], parent=iface_z
    )

    # Create the circuits
    circuit = models.Circuit.objects.create(
        endpoint_a=iface_a, endpoint_z=iface_z
    )
    circuit_for_child_ifaces = models.Circuit.objects.create(
        endpoint_a=child_iface_a, endpoint_z=child_iface_z
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
    assert [str(a) for a in circuit.addresses] == ['10.32.0.1/32', '10.32.0.3/32', \
                                                   '10.32.0.2/32', '10.32.0.4/32']
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


class TestInterfaceFor(object):
    @pytest.fixture
    def device_z(self, site):
        return models.Device.objects.create(site=site, hostname='foo-bar2')

    @pytest.fixture
    def interface_a(self, device):
        return models.Interface.objects.create(device=device, name='eth0')

    @pytest.fixture
    def interface_z(self, device_z):
        return models.Interface.objects.create(
            device=device_z, name='eth0')

    @pytest.fixture
    def normal_circuit(self, device_z, interface_a, interface_z):
        return models.Circuit.objects.create(
            endpoint_a=interface_a,
            endpoint_z=interface_z
        )

    @pytest.fixture
    def looped_circuit(self, device, interface_a):
        interface_z = models.Interface.objects.create(
            device=device,
            name='eth1'
        )
        return models.Circuit.objects.create(
            endpoint_a=interface_a,
            endpoint_z=interface_z,
        )

    def test_normal_conditions(self, device, device_z, interface_a,
                               interface_z, normal_circuit):
        assert normal_circuit.interface_for(device) == interface_a
        print('interface_z via circuit id = {}'.format(normal_circuit.endpoint_z.id))
        print('interface_z id = {}'.format(interface_z.id))
        assert normal_circuit.interface_for(device_z) == interface_z

    def test_single_sided(self, device, interface_a):
        """
        Make sure things don't blow up on a single-sided circuit
        """
        circuit = models.Circuit.objects.create(endpoint_a=interface_a)
        assert circuit.interface_for(device) == interface_a

    def test_looped_circuit(self, device, looped_circuit, interface_a):
        """
        Test the case when both sides of a circuit are connected to the same
        device. The method should return endpoint_a in this case.
        """
        assert looped_circuit.interface_for(device) == interface_a

    def test_bogus_device(self, device, device_z, looped_circuit):
        """
        interface_for should return None when given a device that isn't
        connected by the circuit
        """
        assert looped_circuit.interface_for(device_z) is None
        assert looped_circuit.interface_for(device) is not None
