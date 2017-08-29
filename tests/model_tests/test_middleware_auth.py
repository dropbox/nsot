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

from .fixtures import admin_user, user, site, transactional_db

def test_object_level_permissions_with_ancestors(site, user):
    net_8  = models.Network.objects.create(site=site, cidr=u'8.0.0.0/8')
    net_24 = models.Network.objects.create(site=site, cidr=u'8.0.0.0/24')
    net_16 = models.Network.objects.create(site=site, cidr=u'8.0.0.0/16')

    # Need to refresh the objects from the db so the updated parent_ids are
    # reflected.
    net_8.refresh_from_db()
    net_24.refresh_from_db()
    net_16.refresh_from_db()

    grp = Group.objects.create(name='test_group')
    user.groups.add(grp)

    check_perms = NsotObjectPermissionsBackend()
    assert check_perms.has_perm(user, 'delete_network', net_24) is False

    assign_perm('delete_network', user, net_8)
    assert check_perms.has_perm(user, 'delete_network', net_8) is True
    assert check_perms.has_perm(user, 'delete_network', net_24) is True
