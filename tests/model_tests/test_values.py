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
    """Test explicit value creation."""
    attr = models.Attribute.objects.create(
        resource_name='Device',
        site=site, name='test_attribute'
    )
    dev = models.Device.objects.create(
        hostname='foo-bar1', site=site
    )

    # Explicitly create a Value without providing site_id
    val = models.Value.objects.create(
        obj=dev, attribute=attr, value='foo'
    )

    # Value site should match attribute
    assert val.site == attr.site

    # Device attributes should match a simple dict
    dev.clean_attributes()
    dev.save()
    assert dev.get_attributes() == {'test_attribute': 'foo'}
