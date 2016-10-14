# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

import pytest
# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError as DjangoValidationError
import ipaddress

from nsot import exc, models

from .fixtures import admin_user, user, site, transactional_db
from ..util import load_json


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


def test_next_network_bug_issues_216(site):
    """
    Test for bug where Network.get_next_network() returns the wrong result.

    Ref: https://github.com/dropbox/nsot/issues/216
    """

    # Load and create the Network objects
    objects = load_json('model_tests/data/networks.json')
    [models.Network.objects.create(site=site, **n) for n in objects]

    # Get the parent
    parent = models.Network.objects.get_by_address('10.20.0.0/16')

    # We're expecting that the next /21 is going to be expected_cidr
    expected_cidr = '10.20.192.0/21'
    expected = [ipaddress.ip_network(expected_cidr)]
    next_21 = parent.get_next_network(prefix_length=21)

    assert next_21 == expected


def test_next_network_bug_issues_224(site):
    """
    Test for bug where Network.get_next_network() returns the wrong result.

    Ref: https://github.com/dropbox/nsot/issues/224
    """

    objects = load_json('model_tests/data/networks.json')
    [models.Network.objects.create(site=site, **n) for n in objects]

    # Get the parent
    parent = models.Network.objects.get_by_address('10.20.0.0/16')

    # We're expecting that the next /31 is going to be first_cidr
    first_cidr = '10.20.0.0/31'
    expected = [ipaddress.ip_network(first_cidr)]
    first_31 = parent.get_next_network(prefix_length=31)

    assert first_31 == expected

    # Create the first /31 and get the next one.
    models.Network.objects.create(cidr=first_cidr, site=site)
    next_cidr = '10.20.0.2/31'
    expected = [ipaddress.ip_network(next_cidr)]
    next_31 = parent.get_next_network(prefix_length=31)

    assert next_31 == expected
