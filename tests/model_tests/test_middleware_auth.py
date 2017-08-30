# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm
import pytest
# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import logging

from nsot import exc, models
from nsot.middleware.auth import NsotObjectPermissionsBackend

from .fixtures import test_group, user, site

def test_object_level_permissions_with_ancestors(site, user, test_group):
    """Test to check object level permissions for objects with a
    ``get_ancestors`` method implementation"""
    net_8  = models.Network.objects.create(site=site, cidr=u'8.0.0.0/8')
    net_24 = models.Network.objects.create(site=site, cidr=u'8.0.0.0/24')
    net_16 = models.Network.objects.create(site=site, cidr=u'8.0.0.0/16')

    # Need to refresh the objects from the db so the updated parent_ids are
    # reflected.
    net_8.refresh_from_db()
    net_24.refresh_from_db()
    net_16.refresh_from_db()

    user.groups.add(test_group)

    check_perms = NsotObjectPermissionsBackend()
    assert check_perms.has_perm(user, 'delete_network', net_24) is False

    assign_perm('delete_network', user, net_8)
    assert check_perms.has_perm(user, 'delete_network', net_8) is True
    assert check_perms.has_perm(user, 'delete_network', net_24) is True
