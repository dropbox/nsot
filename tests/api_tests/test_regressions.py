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


from .fixtures import live_server, client, user, site
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, load, filter_networks
)


log = logging.getLogger(__name__)


def test_network_bug_issues_34(client, site):
    """Test set queries for Networks."""

    # URIs
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    # Pre-load the attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the network objects and retreive them for testing.
    client.post(net_uri, data=load('networks.json'))
    net_resp = client.retrieve(net_uri, include_ips=True)
    net_out = net_resp.json()['data']
    networks = net_out['networks']

    # Filter networks w/ attribute hostname=foo-bar1
    expected = copy.deepcopy(net_out)
    wanted = ['192.168.0.0/24', '192.168.0.0/25']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})

    assert_success(
        client.retrieve(net_uri, attributes='hostname=foo-bar1'),
        expected
    )

    # Filter networks w/ attribute hostname=foo-bar1, including IPs
    wanted = ['192.168.0.1/32', '192.168.0.0/24', '192.168.0.0/25']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})

    assert_success(
        client.retrieve(
            net_uri, attributes='hostname=foo-bar1', include_ips=True
        ),
        expected
    )
