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

from .fixtures import user, transactional_db


log = logging.getLogger(__name__)


def test_site_creation():
    site = models.Site.objects.create(
        name='Test Site',
        description='This is a Test Site.'
    )
    sites = models.Site.objects.all()

    assert sites.count() == 1
    assert sites[0].id == site.id
    assert sites[0].name == site.name
    assert sites[0].description == site.description


def test_site_conflict(transactional_db):
    models.Site.objects.create(
        name='Test Site',
        description='This is a Test Site.'
    )

    with pytest.raises(DjangoValidationError):
        models.Site.objects.create(
            name='Test Site',
            description='This is a Test Site.'
        )

    models.Site.objects.create(
        name='Test Site 2',
        description='This is a Test Site.'
    )


def test_site_validation(transactional_db):
    with pytest.raises(exc.ValidationError):
        models.Site.objects.create(
            name=None,
            description='This is a Test Site.'
        )

    with pytest.raises(exc.ValidationError):
        models.Site.objects.create(
            name='',
            description='This is a Test Site.'
        )

    site = models.Site.objects.create(
        name='Test Site',
        description='This is a Test Site.'
    )

    with pytest.raises(exc.ValidationError):
        site.name = ''
        site.save()

    with pytest.raises(exc.ValidationError):
        site.name = None
        site.save()

    site.name = 'Test Site New'
    site.save()
