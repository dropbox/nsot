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

from .fixtures import admin_user, device, site, user, transactional_db


def test_creation(device):
    """Test basic Interface creation."""
    iface = models.Interface.objects.create(
        device=device, name='eth0'
    )

    # Interface inherits Device's site
    assert iface.site == device.site

    # Name can't be blank
    with pytest.raises(exc.ValidationError):
        iface.name = None
        iface.save()


def test_tree_methods(device):
    iface = models.Interface.objects.create(
        device = device, name = 'eth0'
    )
    iface1 = models.Interface.objects.create(
        device = device, name = 'eth0.0', parent = iface
    )
    iface2 = models.Interface.objects.create(
        device = device, name = 'eth0.1', parent = iface
    )
    iface3 = models.Interface.objects.create(
        device = device, name = 'eth0.2', parent = iface1
    )
    iface4 = models.Interface.objects.create(
        device = device, name = 'eth0.3', parent = iface
    )
    assert iface1.parent.id is iface.id
    assert iface3.get_root().id is iface.id

    children = [x.id for x in iface.get_children()]
    expected = [iface1.id, iface2.id, iface4.id]
    children.sort()
    expected.sort()
    assert children == expected

    descendants = [x.id for x in iface.get_descendants()]
    expected = [iface1.id, iface2.id, iface3.id, iface4.id]
    expected.sort()
    descendants.sort()
    assert descendants == expected

    ancestors = [x.id for x in iface3.get_ancestors()]
    expected = [iface1.id, iface.id]
    expected.sort()
    ancestors.sort()
    assert ancestors == expected

    siblings = [x.id for x in iface4.get_siblings()]
    expected = [iface1.id, iface2.id]
    siblings.sort()
    expected.sort()
    assert siblings == expected


def test_speed(device):
    """Test interface speed."""
    iface = models.Interface.objects.create(device=device, name='eth0')

    # Interface inherits default speed.
    assert iface.speed == settings.INTERFACE_DEFAULT_SPEED

    # String integers are ok, and are converted to integers
    iface.speed = '10000'
    iface.save()
    assert iface.speed == 10000

    # Explicit None is ok, and should not be converted to the default
    iface.speed = None
    iface.save()
    assert iface.speed is None

    # Bad strings are bad
    with pytest.raises(exc.ValidationError):
        iface.speed = 'bogus'
        iface.save()

    # Floats are also bad
    with pytest.raises(exc.ValidationError):
        iface.speed = 10.0
        iface.save()


def test_mac_address(device):
    """Test mac_address."""
    iface = models.Interface.objects.create(device=device, name='eth0')
    assert iface.mac_address == settings.INTERFACE_DEFAULT_MAC

    # Bad MAC is bad
    with pytest.raises(exc.ValidationError):
        iface.mac_address = 'bogus'
        iface.save()

    # Set mac by string
    iface.mac_address = '00:00:8E:B1:B5:78'
    iface.save()

    # Set mac by integer
    iface.mac_address = 122191241314
    iface.save()
    iface.refresh_from_db()

    assert iface.mac_address == '00:1c:73:2a:60:62'


def test_type(device):
    """Test types."""
    iface = models.Interface.objects.create(device=device, name='eth0')
    assert iface.type == 6

    # Make sure validation works.
    with pytest.raises(exc.ValidationError):
        iface.type = 'bogus'
        iface.save()

    # None is invalid
    with pytest.raises(exc.ValidationError):
        iface.type = None
        iface.save()


def test_attributes(device):
    """Test that attributes work as expected."""
    models.Attribute.objects.create(
        site=device.site, resource_name='Interface', name='vlan'
    )

    iface = models.Interface.objects.create(
        name='eth0', device=device, attributes={'vlan': '300'}
    )

    assert iface.get_attributes() == {'vlan': '300'}

    # Verify that we can zero out attributes
    iface.set_attributes({})
    assert iface.get_attributes() == {}

    # And make sure no bogus attributes can be set.
    with pytest.raises(exc.ValidationError):
        iface.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        iface.set_attributes({0: 'value'})

    with pytest.raises(exc.ValidationError):
        iface.set_attributes({'key': 0})

    with pytest.raises(exc.ValidationError):
        iface.set_attributes({'made_up': 'value'})


def test_set_addresses(device):
    """Test addresses/assignment."""
    root_network = models.Network.objects.create(
        cidr='10.0.0.0/8', site=device.site
    )
    parent_network = models.Network.objects.create(
        cidr='10.1.1.0/24', site=device.site
    )
    iface = models.Interface.objects.create(device=device, name='eth0')

    # Test set_addresses
    addresses = ['10.1.1.1/32']
    iface.set_addresses(addresses)

    # Test get_addresses
    assert iface.get_addresses() == addresses

    # Test get_networks
    assert iface.get_networks() == [str(parent_network)]

    # Set multiple addresses w/ one existing.
    multi = ['10.1.1.1/32', '10.1.1.2/32']
    iface.set_addresses(multi)

    # Multi addresses should match
    assert iface.get_addresses() == multi

    # Set bad address
    with pytest.raises(exc.ValidationError):
        iface.set_addresses(['bogus'])

    # Test overwrite, which should remove all addresses.
    iface.set_addresses([], overwrite=True)
    assert iface.get_addresses() == []


def test_set_addresses_on_create(device):
    """Test address/assignment on create"""
    root_network = models.Network.objects.create(
        cidr='10.0.0.0/8', site=device.site
    )
    parent_network = models.Network.objects.create(
        cidr='10.1.1.0/24', site=device.site
    )
    addresses = ['10.1.1.1/32', '10.1.1.2/32']

    iface = models.Interface.objects.create(
        device=device, name='eth0', addresses=addresses
    )

    # Test get_addresses
    assert iface.get_addresses() == addresses

    # Test get_networks
    assert iface.get_networks() == [str(parent_network)]


def test_assign_address(device):
    root_network = models.Network.objects.create(
        cidr='10.0.0.0/8', site=device.site
    )
    parent_network = models.Network.objects.create(
        cidr='10.1.1.0/24', site=device.site
    )

    iface = models.Interface.objects.create(device=device, name='eth0')

    # Test assign_address
    cidr = '10.1.1.1/32'
    assign1 = iface.assign_address(cidr)
    iface.clean_addresses()

    # Confirm assignments
    assert iface.get_addresses() == [cidr]
    assert assign1.address.cidr == cidr
    assert iface.get_assignments() == [assign1.to_dict()]

    # What if we try to assign an existing address? (The same address will do.)
    with pytest.raises(exc.ValidationError):
        iface.assign_address(cidr)

    # What if we try to assign a non /32 or /128?
    with pytest.raises(exc.ValidationError):
        iface.assign_address('10.1.1.0/28')

    # If we delete assignment, Network object should persist.
    # import pdb; pdb.set_trace()
    address = models.Network.objects.get_by_address(cidr)
    assign1.delete()
    assert models.Network.objects.get_by_address(address.cidr) == address

    # If we delete address, asignment should go away.
    assign2 = iface.assign_address(cidr)
    address.delete()
    assert list(iface.assignments.all()) == []


def test_device_hostname(device):
    """Test the device_hostname convenience field"""
    intf = models.Interface.objects.create(device=device, name='eth0')

    assert intf.device.hostname == intf.device_hostname

    # Ensure the name still matches after the device is updated
    device.hostname = "foo-baz"
    device.save()
    intf.refresh_from_db()
    assert intf.device.hostname == intf.device_hostname

    # Ensure query by device_hostname works
    intf == models.Interface.objects.get(device_hostname='foo-baz',
                                         name='eth0')


def test_interface_networks_refresh(device):
    """Test the interface parent networks refresh upon reparenting of a
    Network object"""
    cidr = '10.1.1.1/32'
    parent_network = models.Network.objects.create(
        cidr='10.1.1.0/24', site=device.site
    )
    intf_address = models.Network.objects.create(
        cidr=cidr, site=device.site
    )
    intf = models.Interface.objects.create(device=device, name='eth0')
    intf.assign_address(cidr)
    intf.clean_addresses()
    intf.save()
    assert intf.get_networks() == ['10.1.1.0/24']

    new_parent_network = models.Network.objects.create(
        cidr='10.1.1.0/27', site=device.site
    )
    new_parent_network.save()

    intf_obj = models.Interface.objects.get(device=device, name='eth0')
    assert intf_obj.get_networks() == ['10.1.1.0/27']

# TODO(jathan): This isn't implemented yet, but the idea is that there will be
# pluggable parenting/inheritance strategies, with the "SNMP index" strategy as
# the default/built-in (e.g. snmp_index, snmp_parent_index).
def _test_parenting(device):
    pass

    # Test setting interface parent's automatically (by attrs??)

    # Disallow setting non-Interface objects as parent.

# test_retrieve_interfaces
