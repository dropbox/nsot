# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import (ValidationError as DjangoValidationError,
                                    MultipleObjectsReturned)
import logging

from nsot import exc, models

from .fixtures import admin_user, user, site, transactional_db


def test_creation(site):
    attr = models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='test_attribute'
    )

    attributes = models.Attribute.objects.all()

    assert attributes.count() == 1
    assert attributes[0].id == attr.id
    assert attributes[0].site_id == site.id
    assert attributes[0].name == attr.name
    assert attributes[0].required == attr.required


def test_conflict(site):
    models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='test_attribute'
    )

    with pytest.raises(DjangoValidationError):
        models.Attribute.objects.create(
            resource_name='Network',
            site=site, name='test_attribute'
        )

    models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='test_attribute_2'
    )


def test_validation(site, transactional_db):
    with pytest.raises(exc.ValidationError):
        models.Attribute.objects.create(
            resource_name='Network',
            site=site, name=None,
        )

    with pytest.raises(exc.ValidationError):
        models.Attribute.objects.create(
            resource_name='Network',
            site=site, name='',
        )

    attribute = models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='test_attribute'
    )

    with pytest.raises(exc.ValidationError):
        attribute.name = ''
        attribute.save()

    with pytest.raises(exc.ValidationError):
        attribute.name = None
        attribute.save()

    attribute.name = 'test_attribute_new'
    attribute.save()


def test_deletion(site):
    attribute = models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='test_attribute'
    )

    network = models.Network.objects.create(
        cidr='10.0.0.0/8', site=site, attributes={'test_attribute': 'foo'}
    )

    with pytest.raises(ProtectedError):
        attribute.delete()

    network.delete()
    attribute.delete()


def test_required(site):
    attribute_1 = models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='required_1', required=True
    )
    attribute_2 = models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='required_2', required=True
    )

    with pytest.raises(exc.ValidationError):
        network = models.Network.objects.create(
            cidr='10.0.0.0/8', site=site, attributes={}
        )

    with pytest.raises(exc.ValidationError):
        network = models.Network.objects.create(
            site=site, cidr='10.0.0.0/8', attributes={'required_1': 'foo'}
        )

    network = models.Network.objects.create(
        cidr=u'10.0.0.0/8',
        attributes={'required_1': 'foo', 'required_2': 'bar'},
        site=site,
    )


def test_multi(site):
    multi = models.Attribute.objects.create(
        resource_name='Network', display=True,
        site=site, name='multi', multi=True
    )

    not_multi = models.Attribute.objects.create(
        resource_name='Network',
        site=site, name='not_multi', multi=False
    )

    models.Network.objects.create(site=site, cidr='10.0.0.0/8')

    network = models.Network.objects.create(
        site=site, cidr='10.0.0.1',
        attributes={'multi': ['test', 'testing', 'testtttt']}
    )

    with pytest.raises(exc.ValidationError):
        network = models.Network.objects.create(
            site=site, cidr=u'10.0.0.2',
            attributes={'not_multi': ['test', 'testing', 'testtttt']}
        )


def test_constraints(site):
    default = models.Attribute.objects.create(
        resource_name='Network', site=site, name='default'
    )

    allow_empty = models.Attribute.objects.create(
        resource_name='Network', site=site, name='allow_empty',
        constraints={'allow_empty': True}
    )

    pattern = models.Attribute.objects.create(
        resource_name='Network', site=site, name='pattern',
        constraints={'pattern': '\d\d\d+'}
    )

    valid = models.Attribute.objects.create(
        resource_name='Network', site=site, name='valid',
        constraints={'valid_values': ['foo', 'bar', 'baz']}
    )

    # Test that ValidationError is raised when constraints are not a dict
    with pytest.raises(exc.ValidationError):
        models.Attribute.objects.create(
            resource_name='Network', site=site,
            name='invalid', constraints=['foo', 'bar', 'baz']
        )

    network = models.Network.objects.create(site=site, cidr='10.0.0.0/8')

    with pytest.raises(exc.ValidationError):
        network.set_attributes({'default': ''})

    # Test allow_empty
    network.set_attributes({'allow_empty': ''})

    # Test pattern
    with pytest.raises(exc.ValidationError):
        network.set_attributes({'pattern': ''})

    with pytest.raises(exc.ValidationError):
        network.set_attributes({'pattern': 'foo'})

    with pytest.raises(exc.ValidationError):
        network.set_attributes({'pattern': '10'})

    network.set_attributes({'pattern': '100'})
    network.set_attributes({'pattern': '1000000'})

    # Test valid_values
    with pytest.raises(exc.ValidationError):
        network.set_attributes({'valid': 'hello'})

    network.set_attributes({'valid': 'foo'})


def test_set_query(site):
    """Test backend functionality of set queries."""
    site2 = models.Site.objects.create(name='Site 2')

    # Attributes
    models.Attribute.objects.create(
        name='owner', site=site, resource_name='Device'
    )
    models.Attribute.objects.create(
        name='owner', site=site2, resource_name='Device'
    )
    models.Attribute.objects.create(
        name='role', site=site, resource_name='Device'
    )

    # Devices
    device1 = models.Device.objects.create(
        hostname='foo-bar1', attributes={'owner': 'jathan', 'role': 'br'},
        site=site
    )
    device2 = models.Device.objects.create(
        hostname='foo-bar2', attributes={'owner': 'gary', 'role': 'dr'},
        site=site
    )

    # Since we have two attributes named 'owner' in 2 different sites, this
    # should raise an error. (Fix #66)
    with pytest.raises(MultipleObjectsReturned):
        models.Device.objects.set_query('owner=jathan')

    # Now include the site_id
    devices = models.Device.objects.set_query('owner=jathan', site_id=site.id)
    assert list(devices) == [device1]

    # Bad set queries raises an error.
    bad_queries = [None, {}, 3.14, object()]
    for bad_q in bad_queries:
        with pytest.raises(exc.ValidationError):
            models.Network.objects.set_query(bad_q)

    # Make sure that a bogus set query raises a ValidationError
    with pytest.raises(exc.ValidationError):
        models.Device.objects.set_query('role=[ab, bb, cb]')

    # Empty set query is empty result
    empty = models.Network.objects.set_query('')
    assert list(empty) == []

    # Test regex set query matches a union set query.
    union = models.Device.objects.set_query('role=br +role=dr').order_by('id')
    regex = models.Device.objects.set_query('role_regex=[bd]r').order_by('id')
    assert list(union) == list(regex)

    # Test unique set queries
    # Bad query, too many results
    with pytest.raises(exc.ValidationError):
        models.Device.objects.set_query('role=br +role=dr', unique=True)
    # Bad query, no results
    with pytest.raises(exc.ValidationError):
        models.Device.objects.set_query('role=cc', unique=True)
    # Successful with single result
    devices = models.Device.objects.set_query('role=br', unique=True)
    assert list(devices) == [device1]

