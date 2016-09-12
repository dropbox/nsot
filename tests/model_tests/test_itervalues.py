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
        u_id='jasdgijn001',
        iter_key=itr

    )
#    itrv2 = models.IterValue.objects.create(
#        val = 23
#        u_id='jasdgijn002'
#    )

    iterable_val = models.Iterable.objects.values_list('min_val', flat=True)[0]
    iterv_uid = models.IterValue.objects.values_list('u_id', flat=True)[0]

    assert itrv1.iter_key.id == itr.id
    assert itrv1.val == iterable_val
    assert itrv1.u_id == iterv_uid

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
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn001',
        iter_key=itr
    )
    itrv2 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn002',
        iter_key=itr
    )
    itrv3 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr2),
        u_id='jasdgijn001',
        iter_key=itr2
    )
    itrv4 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr2),
        u_id='jasdgijn002',
        iter_key=itr2
    )

    assert models.IterValue.getnext(itr) == 54
    assert itrv2.val == 52
    assert itrv4.val == 1300


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
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn001',
        iter_key=itr
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
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn001',
        iter_key=itr
    )
    itrv2 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn002',
        iter_key=itr
    )
    itrv3 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr2),
        u_id='jasdgijn001',
        iter_key=itr2
    )
    itrv4 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr2),
        u_id='jasdgijn002',
        iter_key=itr2
    )

    models.IterValue.objects.filter(u_id=service_UID).all().delete()

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
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn001',
        iter_key=itr
    )
    itrv2 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr),
        u_id='jasdgijn002',
        iter_key=itr
    )
    itrv3 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr2),
        u_id='jasdgijn001',
        iter_key=itr2
    )
    itrv4 = models.IterValue.objects.create(
        val = models.IterValue.getnext(itr2),
        u_id='jasdgijn002',
        iter_key=itr2
    )

    with pytest.raises(exc.ProtectedError):
        models.Iterable.objects.all().delete()

