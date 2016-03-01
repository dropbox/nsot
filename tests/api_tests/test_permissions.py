# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import copy
from django.core.urlresolvers import reverse
import json
import logging
from rest_framework import status

from .fixtures import live_server, client, user, site, user_client
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, load, get_result
)


log = logging.getLogger(__name__)


def test_permissions(client, user_client, user, site):
    # URIs
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')
    dev_uri = site.list_uri('device')

    # Create an Attribute
    attr_resp = client.create(
        attr_uri, resource_name='Network', name='attr1'
    )
    attr = get_result(attr_resp)
    attr_obj_uri = site.detail_uri('attribute', id=attr['id'])

    # Create a Network
    net_resp = client.create(net_uri, cidr='10.0.0.0/24')
    net = get_result(net_resp)
    net_obj_uri = site.detail_uri('network', id=net['id'])

    # Create a Device
    dev_resp = client.create(dev_uri, hostname='dev1')
    dev = get_result(dev_resp)
    dev_obj_uri = site.detail_uri('device', id=dev['id'])

    # User shouldn't be able to update site or create/update other resources
    # Site
    assert_error(
        user_client.update(site.detail_uri(), name='site1'),
        status.HTTP_403_FORBIDDEN
    )
    # Attribute
    assert_error(
        user_client.create(attr_uri, name='attr2'),
        status.HTTP_403_FORBIDDEN
    )
    assert_error(
        user_client.update(attr_obj_uri, required=True),
        status.HTTP_403_FORBIDDEN
    )
    # Network
    assert_error(
        user_client.create(net_uri, cidr='10.0.0.0/8'),
        status.HTTP_403_FORBIDDEN
    )
    assert_error(
        user_client.update(net_obj_uri, attributes={'attr1': 'foo'}),
        status.HTTP_403_FORBIDDEN
    )
    # Device
    assert_error(
        user_client.create(dev_uri, name='dev2'),
        status.HTTP_403_FORBIDDEN
    )
    assert_error(
        user_client.update(dev_obj_uri, hostname='foobar'),
        status.HTTP_403_FORBIDDEN
    )
