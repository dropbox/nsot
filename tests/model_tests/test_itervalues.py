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

    itrv1 = models.IterValue.objects.create(
        unique_id='jasdgijn001',
        iterable=itr,
        site=site

    )

    iterable_val = models.Iterable.objects.values_list('min_val', flat=True)[0]
    iterv_uid = models.IterValue.objects.values_list('unique_id', flat=True)[0]

    assert itrv1.iterable.id == itr.id
    assert itrv1.value == iterable_val
    assert itrv1.unique_id == iterv_uid

def test_getnext(site):
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
    itrv1 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr,
        site=site
    )
    itrv2 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn002',
        iterable=itr,
        site=site
    )
    itrv3 = models.IterValue.objects.create(
        value = itr2.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr2,
        site=site
    )
    itrv4 = models.IterValue.objects.create(
        value = itr2.get_next_value()[0],
        unique_id='jasdgijn002',
        iterable=itr2,
        site=site
    )

    assert itr.get_next_value()[0] == 54
    assert itrv2.value == 52
    assert itrv4.value == 1300


def test_save(site):
    itr = models.Iterable.objects.create(
        name='test-vlan',
        description='test vlan for testing',
        min_val = 50,
        max_val = 70,
        increment = 2,
        site = site
    )
    itrv1 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr,
        site=site
    )
    itrv1.save()

def test_delete(site):
    "Delete all rows in IterValues given the service identifier criteria"
    service_UID = 'jasdgijn002'
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
    itrv1 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr,
        site=site

    )
    itrv2 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn002',
        iterable=itr,
        site=site

    )
    itrv3 = models.IterValue.objects.create(
        value = itr2.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr2,
        site=site

    )
    itrv4 = models.IterValue.objects.create(
        value = itr2.get_next_value()[0],
        unique_id='jasdgijn002',
        iterable=itr2,
        site=site

    )

    models.IterValue.objects.filter(unique_id=service_UID).all().delete()

def test_protected_delete(site):
    "Delete all rows in IterValues given the service identifier criteria"
    service_UID = 'jasdgijn002'
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
    
    itrv1 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr,
        site=site

    )
    itrv2 = models.IterValue.objects.create(
        value = itr.get_next_value()[0],
        unique_id='jasdgijn002',
        iterable=itr,
        site=site

    )
    itrv3 = models.IterValue.objects.create(
        value = itr2.get_next_value()[0],
        unique_id='jasdgijn001',
        iterable=itr2,
        site=site

    )
    itrv4 = models.IterValue.objects.create(
        value = itr2.get_next_value()[0],
        unique_id='jasdgijn002',
        iterable=itr2,
        site=site

    )
    with pytest.raises(exc.ProtectedError):
        models.Iterable.objects.all().delete()

