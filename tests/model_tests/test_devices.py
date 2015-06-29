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


def test_device_attributes(site):
    models.Attribute.objects.create(
        site=site,
        resource_name='Device', name='owner'
    )

    device = models.Device.objects.create(
        site=site, hostname='foobarhost', attributes={'owner': 'gary'}
    )

    assert device.get_attributes() == {'owner': 'gary'}

    # Verify property successfully zeros out attributes
    device.set_attributes({})
    assert device.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        device.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        device.set_attributes({0: 'value'})

    with pytest.raises(exc.ValidationError):
        device.set_attributes({'key': 0})

    with pytest.raises(exc.ValidationError):
        device.set_attributes({'made_up': 'value'})


def test_retrieve_device(site):
    models.Attribute.objects.create(
        site=site,
        resource_name='Device', name='test'
    )

    device1 = models.Device.objects.create(
        site=site, hostname='device1',
        attributes={'test': 'foo'}
    )
    device2 = models.Device.objects.create(
        site=site, hostname='device2',
        attributes={'test': 'bar'}
    )
    device3 = models.Device.objects.create(
        site=site, hostname='device3'
    )

    assert list(site.devices.all()) == [device1, device2, device3]

    with pytest.raises(ValueError):
        assert site.devices.filter(attributes__name=None, attributes__value='foo')

    assert list(
        site.devices.filter(
            attributes__attribute__name='test'
        ).order_by('id')
    ) == [device1, device2]

    assert list(
        site.devices.filter(
            attributes__attribute__name='test', attributes__value='foo'
        )
    ) == [device1]
