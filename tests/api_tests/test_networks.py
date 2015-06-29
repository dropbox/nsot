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


def test_creation(live_server, user, site):
    admin_client = Client(live_server, 'admin')
    user_client = Client(live_server, 'user')

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    admin_client.create(attr_uri, resource_name='Network', name='attr1')

    # Invalid permissions
    assert_error(
        user_client.create(
            net_uri, cidr='10.0.0.0/24', attributes={'attr1': 'foo'}
        ),
        status.HTTP_403_FORBIDDEN
    )

    # Missing required field (cidr)
    assert_error(
        admin_client.create(net_uri, attributes={'attr1': 'foo'}),
        status.HTTP_400_BAD_REQUEST
    )

    # Null cidr
    assert_error(
        admin_client.create(net_uri, cidr=None),
        status.HTTP_400_BAD_REQUEST
    )

    # Verify Successful Creation
    net_resp = admin_client.create(
        net_uri, cidr='10.0.0.0/24', attributes={'attr1': 'foo'}
    )
    net = net_resp.json()['data']['network']
    net_obj_uri = site.detail_uri('network', id=net['id'])

    assert_created(net_resp, net_obj_uri)

    # Verify Successful get of all Networks
    expected = net_resp.json()['data']
    expected['networks'] = [expected.pop('network')]
    expected.update({'limit': None, 'offset': 0, 'total': 1})

    assert_success(admin_client.get(net_uri), expected)

    # Verify Successful get of single Network
    assert_success(admin_client.get(net_obj_uri), {'network': net})


def test_collection_creation(site, client):
    # URIs
    net_uri = site.list_uri('network')

    # Successfully create a collection of Networks
    collection = [
        {'cidr': '1.1.1.0/24'},
        {'cidr': '2.2.2.0/24'},
        {'cidr': '3.3.3.0/24'},
    ]
    collection_response = client.post(
        net_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Networks
    output = collection_response.json()
    output['data'].update({
        'limit': None, 'offset': 0, 'total': len(collection)
    })

    assert_success(client.get(net_uri), output['data'])


def test_filters(site, client):
    """Test cidr/address/prefix/attribute filters for Networks."""

    # URIs
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the network objects and retreive them for testing.
    client.post(net_uri, data=load('networks.json'))
    net_resp = client.retrieve(net_uri, include_ips=True)
    net_out = net_resp.json()['data']
    networks = net_out['networks']

    # Test lookup by cidr
    expected = copy.deepcopy(net_out)
    wanted = ['10.0.0.0/8']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(net_uri, cidr='10.0.0.0/8'),
        expected
    )

    # Test lookup by attributes
    wanted = ['192.168.0.0/16', '172.16.0.0/12']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(net_uri, attributes='foo=baz'),
        expected
    )

    # Test lookup with multiple attributes
    wanted = ['172.16.0.0/12']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(net_uri, attributes=['foo=baz', 'cluster=lax']),
        expected
    )

    # Test lookup by network_address
    wanted = ['169.254.0.0/16']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(net_uri, network_address='169.254.0.0'),
        expected
    )

    # Test lookup by prefix_length
    wanted = ['192.168.0.0/16', '169.254.0.0/16']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(net_uri, prefix_length=16),
        expected
    )


    # Test lookup by network_address + prefix_length
    wanted = ['10.0.0.0/8']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(net_uri, network_address='10.0.0.0', prefix_length=8),
        expected
    )


def test_set_queries(client, site):
    """Test set queries for Networks."""

    # URIs
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')
    query_uri = site.query_uri('network')

    # Pre-load the attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the network objects and retreive them for testing.
    client.post(net_uri, data=load('networks.json'))
    net_resp = client.retrieve(net_uri, include_ips=True)
    net_out = net_resp.json()['data']
    networks = net_out['networks']

    # INTERSECTION: foo=bar
    expected = copy.deepcopy(net_out)
    wanted = ['10.0.0.0/8', '169.254.0.0/16']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='foo=bar'),
        expected
    )

    # INTERSECTION: foo=bar owner=jathan
    wanted = ['169.254.0.0/16']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='foo=bar owner=jathan'),
        expected
    )

    # DIFFERENCE: -owner=gary
    wanted = ['192.168.0.0/16', '169.254.0.0/16', '192.168.0.0/24',
              '192.168.0.0/25']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='-owner=gary'),
        expected
    )

    # UNION: cluster +foo=baz
    wanted = ['192.168.0.0/16', '172.16.0.0/12']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='cluster +foo=baz'),
        expected
    )

    # Test that include_ips=True actually does that.
    wanted = ['192.168.0.1/32']
    expected['networks'] = filter_networks(networks, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='vlan=300', include_ips=True),
        expected
    )


def test_update(live_server, user, site):
    admin_client = Client(live_server, 'admin')
    user_client = Client(live_server, 'user')

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    admin_client.create(attr_uri, resource_name='Network', name='attr1')
    net_resp = admin_client.create(
        net_uri, cidr='10.0.0.0/24', attributes={'attr1': 'foo'}
    )

    # Extract the Network object so that we can play w/ it during update tests.
    net = net_resp.json()['data']['network']
    net_obj_uri = site.detail_uri('network', id=net['id'])

    # Empty Update should only clear attributes.
    params = {'attributes': {}}
    net.update(params)

    assert_success(
        admin_client.update(net_obj_uri, **params),
        {'network': net}
    )

    # Now put attributes back
    params['attributes'] = {'attr1': 'foo'}
    net.update(params)

    assert_success(
        admin_client.update(net_obj_uri, **params),
        {'network': net}
    )

    # Invalid permissions
    assert_error(user_client.update(net_obj_uri), status.HTTP_403_FORBIDDEN)


def test_deletion(site, client):
    net_uri = site.list_uri('network')
    attr_uri = site.list_uri('attribute')

    net1_resp = client.create(net_uri, cidr='10.0.0.0/24')
    net1 = net1_resp.json()['data']['network']
    net1_obj_uri = site.detail_uri('network', id=net1['id'])

    net2_resp = client.create(net_uri, cidr='10.0.0.1/32')
    net2 = net2_resp.json()['data']['network']
    net2_obj_uri = site.detail_uri('network', id=net2['id'])

    # Don't allow delete when there's an attached subnet/ip
    assert_error(client.delete(net1_obj_uri), status.HTTP_409_CONFLICT)

    # Delete the child Network
    client.delete(net2_obj_uri)

    # And safely delete the parent Network
    assert_deleted(client.delete(net1_obj_uri))
