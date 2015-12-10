# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import copy
from django.core.urlresolvers import reverse
from django.conf import settings
import json
import logging
from rest_framework import status


from .fixtures import live_server, client, user, site
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, load, filter_networks, make_mac
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
    net_resp = client.retrieve(net_uri)
    net_out = net_resp.json()['data']
    networks = net_out['networks']

    # Filter networks w/ attribute hostname=foo-bar1, excluding IPs
    expected = copy.deepcopy(net_out)
    wanted = ['192.168.0.0/24', '192.168.0.0/25']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})

    assert_success(
        client.retrieve(
            net_uri, attributes='hostname=foo-bar1', include_ips=False
        ),
        expected
    )

    # Filter networks w/ attribute hostname=foo-bar1, including IPs
    wanted = ['192.168.0.1/32', '192.168.0.0/24', '192.168.0.0/25']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})

    assert_success(
        client.retrieve(
            net_uri, attributes='hostname=foo-bar1'
        ),
        expected
    )


def test_mac_address_bug_issues_111(client, site):
    """Test that a MAC coming in as an integer is properly formatted."""
    # Make sure that none of them ever match wrong.
    mac_int = 122191241314
    mac_str = '122191241314'
    mac_expected = '00:1c:73:2a:60:62'
    mac_wrong = '12:21:91:24:13:14'

    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = dev_resp.json()['data']['device']

    # Create the interface w/ an integer
    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', parent_id=None,
        mac_address=mac_int
    )
    ifc = ifc_resp.json()['data']['interface']
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Test that integer matches expected
    assert make_mac(ifc['mac_address']) == mac_expected

    # Update the interface w/ a string integer
    updated = copy.deepcopy(ifc)
    updated_resp = client.put(ifc_obj_uri, data=json.dumps(updated))
    expected = updated_resp.json()['data']['interface']

    # Test that string integer matches expectd
    assert make_mac(expected['mac_address']) == mac_expected

    # And for completeness, make sure that a formatted string still comes back
    # the same.
    updated['mac_address'] = mac_expected
    updated_resp = client.put(ifc_obj_uri, data=json.dumps(updated))
    expected = updated_resp.json()['data']['interface']

    # Test that expected matches expected
    assert make_mac(expected['mac_address']) == mac_expected


def test_options_bug_issues_126(client, site):
    """
    Test that OPTIONS query returns a 200 OK and has content.

    Ref: https://github.com/dropbox/nsot/issues/126
    """
    net_uri = site.list_uri('network')

    opts_resp = client.options(net_uri)

    # Assert 200 OK
    assert opts_resp.status_code == 200

    # Assert payload is a thing.
    expected = [u'actions', u'description', u'name', u'parses', u'renders']
    assert sorted(opts_resp.json()) == expected
