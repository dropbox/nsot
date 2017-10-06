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


def test_create_basic_iterable(site):
    vrf = models.Iterable.objects.create(
        site=site,
        name='my_vrf',
        description='Dummy Test VRF',
        min_val=5500,
        max_val=6000,
        increment=1
    )

    basic = models.Iterable.objects.all()

    assert basic.count() == 1
    assert basic[0].id == vrf.id
    assert basic[0].name == vrf.name
    assert basic[0].min_val == vrf.min_val
    assert basic[0].max_val == vrf.max_val
    assert basic[0].increment == vrf.increment
    assert basic[0].parent is None
    assert basic[0].site_id == site.id 


def test_sequential_creation(site):
    vlan1 = models.Iterable.objects.create(
        site=site,
        name='vlan1',
        description='New Test Vlan',
        min_val=50,
        max_val=70,
        increment=1
    )
    
    vlan1.refresh_from_db()

    vlan2 = models.Iterable.objects.create(
        site=site,
        name='vlan2',
        description='Test Vlan2',
        parent=vlan1,
        value=50
    )

    iterables = models.Iterable.objects.all()

    assert iterables.count() == 2
    assert iterables[0].name == vlan1.name
    assert vlan2.parent_id == vlan1.id
    assert vlan1.parent_id is None
    assert vlan2.value == 50
    assert vlan1.value is None


def test_next_value(site):
    iterable_1 = models.Iterable.objects.create(
        site=site,
        name='iterable1',
        min_val=100,
        max_val=1000,
        increment=1,
        description='My favorite iterable'
    )

    iterables = models.Iterable.objects.all()

    next_itr = iterables[0].get_next_value()

    assert iterables.count() == 1
    assert next_itr[0] == 100

def test_delete_iterable(site):
    vrf_1 = models.Iterable.objects.create(
        site=site,
        name='test_to_delete',
        min_val=100,
        max_val=1000,
        increment=1,
        description='test'
    )

    itrs = models.Iterable.objects.all()

    assert itrs.count() == 1
    assert itrs[0].name == vrf_1.name

    vrf_1.delete()
    itrs_2 = models.Iterable.objects.all()

    assert itrs_2.count() == 0

def test_lookup_iterable(site):
    attrs_to_create = ['service_type', 'type', 'device_segment', 'network_segment']
    for attr in attrs_to_create:
        models.Attribute.objects.create(
            site=site,
            resource_name='Iterable', name=attr
        )

    vrf_1 = models.Iterable.objects.create(
        site=site,
        name='vrf_test',
        min_val=100,
        max_val=1000,
        increment=1,
        attributes={
            'service_type': 'vrf',
            'type': 'incrementing',
            'device_segment': 'routing',
            'network_segment': 'cloud'
        }
    )

    vlan_1 = models.Iterable.objects.create(
        site=site,
        name='vlan_test',
        min_val=100,
        max_val=1000,
        increment=1,
        attributes={
            'service_type': 'vlan',
            'type': 'incrementing',
            'device_segment': 'switching',
            'network_segment': 'wan'
        }
    )

    asset_tag_1 = models.Iterable.objects.create(
        site=site,
        name='asset_tag_test',
        min_val=10,
        max_val=9999,
        increment=1,
        attributes={
            'service_type': 'cmdb',
            'type': 'incrementing',
            'device_segment': 'user',
            'network_segment': 'lan'
        }
    )

    vlan_2 = models.Iterable.objects.create(
        site=site,
        name='vlan_test',
        min_val=100,
        max_val=1000,
        value=100,
        parent=vlan_1,
        increment=1,
        attributes={
            'service_type': 'vlan',
            'type': 'incrementing',
            'device_segment': 'switching',
            'network_segment': 'wan'
        }
    )

    assert list(site.iterable.filter(parent_id=None)) == [vrf_1, vlan_1, asset_tag_1]
    assert list(site.iterable.filter(parent_id=vlan_1)) == [vlan_2]
    assert list(site.iterable.by_attribute('service_type', 'vlan')) == [vlan_1, vlan_2]
    assert list(site.iterable.by_attribute('type', 'incrementing')) == [vrf_1, vlan_1, asset_tag_1, vlan_2]
    assert vlan_1.get_next_value()[0] == 101