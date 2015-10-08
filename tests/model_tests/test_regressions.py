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


def test_reparent_bug_issues_27(site):
    """
    Test for bug described at https://github.com/dropbox/nsot/issues/27
    """

    net_8  = models.Network.objects.create(site=site, cidr=u"10.0.0.0/8")
    net_31 = models.Network.objects.create(site=site, cidr=u"10.17.244.128/31")
    net_25 = models.Network.objects.create(site=site, cidr=u"10.16.1.0/25")

    net_8.refresh_from_db()
    net_31.refresh_from_db()
    net_25.refresh_from_db()

    assert net_8.parent_id is None
    assert net_31.parent_id == net_8.id
    assert net_25.parent_id == net_8.id


def test_nonexistent_attr_issues_99(site):
    """
    Test that set query on non-existent attribute returns an empty list.

    Ref: https://github.com/dropbox/nsot/issues/99
    """

    dev = models.Device.objects.create(site=site, hostname='foo-bar1')
    models.Interface.objects.create(device=dev, name='eth0')
    all_interfaces = models.Interface.objects.all()

    assert list(models.Interface.objects.set_query('bad=bogus')) == []
    assert list(all_interfaces.set_query('fake=notreal')) == []
