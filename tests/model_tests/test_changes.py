# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError as DjangoValidationError
import ipaddress
import json
import logging
import re

from nsot import exc, models

from .fixtures import device, user, site


# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db


@pytest.fixture
def create(device, user):
    models.Change.objects.create(event='Create', obj=device, user=user)


def test_diff_device_hostname(create, device, user):
    device.hostname = 'foo-bar3'
    device.save()
    update = models.Change.objects.create(event='Update', obj=device,
                                          user=user)

    assert '-   "hostname": "foo-bar1"' in update.diff
    assert '+   "hostname": "foo-bar3"' in update.diff


def test_diff_noop(create, device, user):
    update = models.Change.objects.create(event='Update', obj=device,
                                          user=user)

    blob = json.dumps(update.resource, indent=2, sort_keys=True)

    for line_a, line_b in zip(update.diff.splitlines(), blob.splitlines()):
        assert line_a.strip() == line_b.strip()


def test_diff_delete(create, device, user):
    delete = models.Change.objects.create(event='Delete', obj=device,
                                          user=user)
    blob = json.dumps(delete.resource, indent=2, sort_keys=True)

    for line_a, line_b in zip(delete.diff.splitlines(), blob.splitlines()):
        assert line_a == '- ' + line_b
