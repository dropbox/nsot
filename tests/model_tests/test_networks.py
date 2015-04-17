# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError as DjangoValidationError
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
