# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError as DjangoValidationError
import ipaddress
import logging

from nsot import exc, models

from .fixtures import admin_user, user, site, transactional_db


def test_networks_creation_reparenting(site):
    net_8  = models.Network.objects.create(site=site, cidr=u'10.0.0.0/8')
    net_24 = models.Network.objects.create(site=site, cidr=u'10.0.0.0/24')
    net_16 = models.Network.objects.create(site=site, cidr=u'10.0.0.0/16')
    net_0  = models.Network.objects.create(site=site, cidr=u'0.0.0.0/0')

    # Need to refresh the objects from the db so the updated parent_ids are
    # reflected.
    net_8.refresh_from_db()
    net_24.refresh_from_db()
    net_16.refresh_from_db()
    net_0.refresh_from_db()

    assert net_0.parent_id is None
    assert net_8.parent_id == net_0.id
    assert net_16.parent_id == net_8.id
    assert net_24.parent_id == net_16.id

    assert list(net_0.supernets()) == []
    assert list(
        net_0.subnets().order_by('network_address', 'prefix_length')
    ) == [net_8, net_16, net_24]

    assert list(net_8.supernets()) == [net_0]
    assert list(net_8.subnets()) == [net_16, net_24]

    assert list(net_16.supernets()) == [net_0, net_8]
    assert list(net_16.subnets()) == [net_24]

    assert list(
        net_24.supernets().order_by('network_address', 'prefix_length')
    ) == [net_0, net_8, net_16]
    assert list(net_24.subnets()) == []


def test_seqential_creation(site):
    net_8 = models.Network.objects.create(site=site, cidr=u'10.0.0.0/8')
    net_22_1 = models.Network.objects.create(site=site, cidr=u'10.0.0.0/22')
    net_22_2 = models.Network.objects.create(site=site, cidr=u'10.0.4.0/22')
    net_22_3 = models.Network.objects.create(site=site, cidr=u'10.0.8.0/22')

    net_8.refresh_from_db()
    net_22_1.refresh_from_db()
    net_22_2.refresh_from_db()
    net_22_3.refresh_from_db()

    assert net_8.id == net_22_1.parent_id
    assert net_8.id == net_22_2.parent_id
    assert net_8.id == net_22_3.parent_id


def test_network_create_hostbits_set(site):
    with pytest.raises(exc.ValidationError):
        models.Network.objects.create(site=site, cidr=u'10.0.0.0/0')


def test_network_attributes(site):
    models.Attribute.objects.create(
        site=site,
        resource_name='Network', name='vlan'
    )

    network = models.Network.objects.create(
        site=site, cidr=u'10.0.0.0/8', attributes={'vlan': '34' }
    )

    assert network.get_attributes() == {'vlan': '34'}

    # Verify property successfully zeros out attributes
    network.set_attributes({})
    assert network.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        network.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        network.set_attributes({0: 'value'})

    with pytest.raises(exc.ValidationError):
        network.set_attributes({'key': 0})

    with pytest.raises(exc.ValidationError):
        network.set_attributes({'made_up': 'value'})


def test_ip_address_no_network(site):
    with pytest.raises(exc.ValidationError):
        models.Network.objects.create(site=site, cidr=u'10.0.0.1/32')

    models.Network.objects.create(site=site, cidr=u'10.0.0.0/8')
    models.Network.objects.create(site=site, cidr=u'10.0.0.1/32')


def test_retrieve_networks(site):
    models.Attribute.objects.create(
        site=site, resource_name='Network', name='test'
    )

    net_8 = models.Network.objects.create(
        site=site, cidr=u'10.0.0.0/8', attributes={'test': 'foo'}
    )
    net_24 = models.Network.objects.create(
        site=site, cidr=u'10.0.0.0/24', attributes={'test': 'bar'}
    )
    ip = models.Network.objects.create(
        site=site, cidr=u'10.0.0.1/32'
    )

    # root=True
    assert list(site.networks.filter(parent_id=None)) == [net_8]


    # include_networks=True, include_ips=Fals
    assert list(site.networks.filter(is_ip=False)) == [net_8, net_24]

    # include_networks=False, include_ips=False
    assert list(site.networks.none()) == []

    # include_networks=True, include_ips=True
    assert list(site.networks.all()) == [net_8, net_24, ip]

    # include_networks=False, include_ips=True
    assert list(site.networks.filter(is_ip=True)) == [ip]

    # There is no use-case for these tests.
    '''
    assert sorted(site.networks(
        subnets_of='10.0.0.0/10'
    )) == sorted([net_24])

    assert sorted(site.networks(
        subnets_of='10.0.0.0/10', include_ips=True
    )) == sorted([net_24, ip])

    assert sorted(site.networks(
        supernets_of='10.0.0.0/10'
    )) == sorted([net_8])

    with pytest.raises(ValueError):
        site.networks(subnets_of='10.0.0.0/10', supernets_of='10.0.0.0/10')
    '''

    with pytest.raises(ValueError):
        assert site.networks.filter(
            attributes__name=None, attributes__value='foo'
        )

    assert list(
        site.networks.filter(attributes__attribute__name='test').order_by('id')
    ) == [net_8, net_24]

    assert list(
        site.networks.filter(
            attributes__attribute__name='test', attributes__value='foo'
        )
    ) == [net_8]


def test_mptt_methods(site):
    """Test ancestor/children/descendents/root model methods."""
    net_8 = models.Network.objects.create(site=site, cidr=u'10.0.0.0/8')
    net_12 = models.Network.objects.create(site=site, cidr=u'10.16.0.0/12')
    net_14 = models.Network.objects.create(site=site, cidr=u'10.16.0.0/14')
    net_25 = models.Network.objects.create(site=site, cidr=u'10.16.2.0/25')
    ip1 = models.Network.objects.create(site=site, cidr=u'10.16.2.1/32')
    ip2 = models.Network.objects.create(site=site, cidr=u'10.16.2.2/32')

    for obj in (net_8, net_12, net_14, net_25, ip1, ip2):
        obj.refresh_from_db()

    # is_child_node()
    assert ip1.is_child_node()
    assert net_25.is_child_node()
    assert not net_8.is_child_node()

    # is_leaf_node()
    assert ip1.is_leaf_node()
    assert not net_25.is_leaf_node()

    # is_root_node()
    assert net_8.is_root_node()
    assert not net_25.is_root_node()

    # get_ancestors()
    assert list(net_25.get_ancestors()) == [net_8, net_12, net_14]
    assert list(net_25.get_ancestors(ascending=True)) == [net_14, net_12, net_8]

    # get_children()
    assert list(net_25.get_children()) == [ip1, ip2]
    assert list(net_12.get_children()) == [net_14]

    # get_descendents()
    assert list(net_8.get_descendents()) == [net_12, net_14, net_25, ip1, ip2]
    assert list(net_14.get_descendents()) == [net_25, ip1, ip2]
    assert list(ip2.get_descendents()) == []

    # get_root()
    assert ip1.get_root() == net_8
    assert net_8.get_root() is None

    # get_siblings()
    assert list(ip1.get_siblings()) == [ip2]
    assert list(ip1.get_siblings(include_self=True)) == [ip1, ip2]

    net_192_1 = models.Network.objects.create(site=site, cidr=u'192.168.1.0/24')
    net_192_2 = models.Network.objects.create(site=site, cidr=u'192.168.2.0/24')

    for obj in (net_8, net_192_1, net_192_2):
        obj.refresh_from_db()

    assert list(net_8.get_siblings()) == [net_192_1, net_192_2]
    assert list(net_192_1.get_siblings()) == [net_8, net_192_2]
    assert list(net_192_2.get_siblings(include_self=True)) == [net_8, net_192_1, net_192_2]


def test_get_next_methods(site):
    """Test the methods for getting next available networks/addresses."""
    net_25 = models.Network.objects.create(site=site, cidr=u'10.16.2.0/25')
    net_29 = models.Network.objects.create(site=site, cidr=u'10.16.2.8/29')
    ip1 = models.Network.objects.create(site=site, cidr=u'10.16.2.1/32')
    ip2 = models.Network.objects.create(site=site, cidr=u'10.16.2.2/32')
    ip3 = models.Network.objects.create(site=site, cidr=u'10.16.2.17/32')

    for obj in (net_25, net_29, ip1, ip2, ip3):
        obj.refresh_from_db()

    #
    # get_next_network()
    #

    # A single /28
    assert net_25.get_next_network(28) == [ipaddress.ip_network(u'10.16.2.16/28')]

    # 4x /27
    slash27 = [u'10.16.2.0/27', u'10.16.2.32/27', u'10.16.2.64/27', u'10.16.2.96/27']
    expected = [ipaddress.ip_network(n) for n in slash27]
    assert net_25.get_next_network(27, num=4) == expected

    # as_objects=False
    assert net_25.get_next_network(27, num=4, as_objects=False) == slash27

    # 5x /27 will still only return 4
    assert net_25.get_next_network(27, num=5) == expected

    # If we try to get a /25 and we are a /25, we get nothing!
    assert net_25.get_next_network(25) == []

    # Invalid prefix
    with pytest.raises(exc.ValidationError):
        net_25.get_next_network(42)

    # Prefix out of bounds
    with pytest.raises(exc.ValidationError):
        net_25.get_next_network(24)

    # Invalid num
    with pytest.raises(exc.ValidationError):
        net_25.get_next_network(28, num='infinity')

    #
    # get_next_address()
    #

    # A single /32
    assert net_25.get_next_address() == [ipaddress.ip_network(u'10.16.2.18/32')]

    # 3x /32
    slash32 = [u'10.16.2.18/32', u'10.16.2.19/32', u'10.16.2.20/32']
    objects = [ipaddress.ip_network(s) for s in slash32]
    assert net_25.get_next_address(num=3) == objects

    # Make sure that 1st/last address is never allocated.
    bad = (u'10.16.2.8/32', u'10.16.2.15/32')
    addresses = net_29.get_next_address(num=8)
    for bad_addr in [ipaddress.ip_network(b) for b in bad]:
        assert bad_addr not in addresses

    # as_objects=False
    assert net_25.get_next_address(num=3, as_objects=False) == slash32
