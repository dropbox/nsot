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
        min_val = 50,
        max_val = 70,
        increment = 2,
        site = site
    )

    iterable = models.Iterable.objects.all()

    assert iterable.count() == 1
    assert iterable[0].id == itr.id
    assert iterable[0].site_id == site.id
    assert iterable[0].name == itr.name
    assert iterable[0].min_val == itr.min_val
    assert iterable[0].max_val == itr.max_val
    assert iterable[0].increment == itr.increment

def test_save(site):
    iterable = models.Iterable.objects.create(
        name='testsave',
        description='testsave Iterable',
        min_val = 50,
        max_val = 70,
        increment = 2,
        site = site
    )

    iterable.save()

def test_deletion(site):
    iterable = models.Iterable.objects.create(
        name='test2',
        description='test2 Iterable',
        min_val = 50,
        max_val = 70,
        increment = 2,
        site = site
    )

    iterable.delete()

