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
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 1,
        max_val = 70,
        increment = 2,
        site = site
    )
    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )


    itrv1 = models.Itervalue.objects.create(
        iterable=itr,
        site=site,
        attributes={'service_key': 'skey_custA_01'}
    )


    assert itrv1.iterable.id == itr.id
    assert itrv1.get_attributes() == {'service_key': 'skey_custA_01'}
    #Validate per tests in test_devices
    itrv1.set_attributes({})
    assert itrv1.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        itrv1.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        itrv1.set_attributes({0: 'value'})

    with pytest.raises(exc.ValidationError):
        itrv1.set_attributes({'key': 0})

    with pytest.raises(exc.ValidationError):
        itrv1.set_attributes({'made_up': 'value'})

def test_getnext(site):
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 5,
        max_val = 70,
        increment = 2,
        site = site
    )
    itr2 = models.Iterable.objects.create(
        name='test-vrf',
        description='test vrf for testing',
        min_val = 1200,
        max_val = 2200,
        increment = 100,
        site = site
    )
    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )
    itrv1 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custA_01'},
        iterable=itr,
        site=site
    )
    itrv2 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custA_02'},
        iterable=itr,
        site=site
    )
    itrv3 = models.Itervalue.objects.create(
        value = itr2.get_next_value()[0],
        attributes={'service_key': 'skey_custB_01'},
        iterable=itr2,
        site=site
    )
    itrv4 = models.Itervalue.objects.create(
        value = itr2.get_next_value()[0],
        attributes={'service_key': 'skey_custB_02'},
        iterable=itr2,
        site=site
    )

    assert itr.get_next_value()[0] == 9
    assert itrv2.value == 7
    assert itrv4.value == 1300

def test_retrive(site):
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 150,
        max_val = 170,
        increment = 2,
        site = site
    )
    itr2 = models.Iterable.objects.create(
        name='test-vrf',
        description='test vrf for testing',
        min_val = 1200,
        max_val = 2200,
        increment = 100,
        site = site
    )
    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )
    itrv1 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custA_01'},
        iterable=itr,
        site=site
    )
    itrv2 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custA_02'},
        iterable=itr,
        site=site
    )
    itrv3 = models.Itervalue.objects.create(
        value = itr2.get_next_value()[0],
        attributes={'service_key': 'skey_custB_01'},
        iterable=itr2,
        site=site
    )
    itrv4 = models.Itervalue.objects.create(
        value = itr2.get_next_value()[0],
        attributes={'service_key': 'skey_custB_02'},
        iterable=itr2,
        site=site
    )

    assert list(site.itervalue.all()) == [itrv1, itrv2, itrv3, itrv4]

    #Retrive by attribute
    assert list(site.itervalue.by_attribute('service_key', 'skey_custB_02')) == [ itrv4 ]
    assert list(site.itervalue.by_attribute('service_key', 'skey_custB_01')) == [ itrv3 ]
    assert list(site.itervalue.by_attribute('service_key', 'skey_custA_02')) == [ itrv2 ]
    assert list(site.itervalue.by_attribute('service_key', 'skey_custA_01')) == [ itrv1 ]

def test_save(site):
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 22,
        max_val = 99,
        increment = 2,
        site = site
    )
    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )

    itrvX = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custX_01'},
        iterable=itr,
        site=site
    )
    itrvX.save()

def test_delete(site):
    "Delete all rows in Itervalues given the service identifier criteria"
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 50,
        max_val = 70,
        increment = 2,
        site = site
    )
    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )

    itrv1 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custB_02'},
        iterable=itr,
        site=site
    )
    site.itervalue.by_attribute('service_key', 'skey_custB_02').delete()

def test_duplicate_values(site):
    "Test that duplicate itervalues cannot exist"
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 500,
        max_val = 700,
        increment = 2,
        site = site
    )
    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )

    itrv1 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0], #This should assign the value 50
        attributes={'service_key': 'skey_custA_01'},
        iterable=itr,
        site=site

    )
    itrv1.save()

    itrv2 = models.Itervalue.objects.create(
        value = 500, #Try to manually assign duplicate value
        attributes={'service_key': 'skey_custA_02'},
        iterable=itr,
        site=site
    )
    with pytest.raises(exc.ValidationError):
        itrv2.save() #The model should catch the dupe and raise an E

    site.itervalue.by_attribute('service_key', 'skey_custA_01').delete()



def test_protected_delete(site):
    "Delete all rows in Itervalues given the service identifier criteria"
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 50,
        max_val = 70,
        increment = 2,
        site = site
    )
    itr2 = models.Iterable.objects.create(
        name='test-vrf',
        description='test vrf for testing',
        min_val = 1200,
        max_val = 2200,
        increment = 100,
        site = site
    )

    #Create the Attribute
    models.Attribute.objects.create(
        site=site,
        resource_name='Itervalue', name='service_key'
    )


    itrv1 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custA_01'},
        iterable=itr,
        site=site

    )
    itrv2 = models.Itervalue.objects.create(
        value = itr.get_next_value()[0],
        attributes={'service_key': 'skey_custA_02'},
        iterable=itr,
        site=site

    )
    itrv3 = models.Itervalue.objects.create(
        value = itr2.get_next_value()[0],
        attributes={'service_key': 'skey_custB_01'},
        iterable=itr2,
        site=site

    )
    itrv4 = models.Itervalue.objects.create(
        value = itr2.get_next_value()[0],
        attributes={'service_key': 'skey_custB_02'},
        iterable=itr2,
        site=site

    )
    with pytest.raises(exc.ProtectedError):
        models.Iterable.objects.all().delete()
