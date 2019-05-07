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
    Client, load, filter_networks, mkcidr, get_result
)


log = logging.getLogger(__name__)


def test_creation(live_server, user, site):
    """Test creation of Networks."""
    admin_client = Client(live_server, 'admin')
    user_client = Client(live_server, 'user')
    cidr = '10.0.0.0/24'

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    admin_client.create(attr_uri, resource_name='Network', name='attr1')

    # Invalid permissions
    assert_error(
        user_client.create(
            net_uri, cidr=cidr, attributes={'attr1': 'foo'}
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
        net_uri, cidr=cidr, attributes={'attr1': 'foo'},
        state='reserved',
    )
    net = get_result(net_resp)
    net_obj_uri = site.detail_uri('network', id=net['id'])

    assert_created(net_resp, net_obj_uri)

    # Verify Successful get of all Networks
    payload = get_result(net_resp)
    expected = [payload]

    assert_success(admin_client.get(net_uri), expected)

    # Verify Successful get of single Network
    assert_success(admin_client.get(net_obj_uri), net)

    # Verify successful get of single Network by natural_key
    net_natural_uri = site.detail_uri('network', id=cidr)
    assert_success(admin_client.get(net_natural_uri), net)

    # Test creation by network_address, prefix_length
    params = {'network_address': '10.8.0.0', 'prefix_length': 16}
    net2_resp = admin_client.create(net_uri, **params)
    net2 = get_result(net2_resp)
    net2_obj_uri = site.detail_uri('network', id=net2['id'])
    assert_created(net2_resp, net2_obj_uri)

    # Delete it and then re-recreate it w/ the original payload
    assert_deleted(admin_client.delete(net2_obj_uri))
    net2a_resp = admin_client.create(net_uri, **params)
    net2a = get_result(net2a_resp)
    net2a_obj_uri = site.detail_uri('network', id=net2a['id'])
    assert_created(net2a_resp, net2a_obj_uri)


def test_bulk_operations(site, client):
    """Test creating/updating multiple Networks at once."""
    # URIs
    attr_uri = site.list_uri('attribute')
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
    payload = get_result(output)

    assert_success(client.get(net_uri), payload)

    # Test bulk update to add attributes to each Network
    client.create(attr_uri, resource_name='Network', name='vlan')
    updated = copy.deepcopy(payload)
    for item in updated:
        item['attributes'] = {'vlan': '300'}
    updated_resp = client.put(net_uri, data=json.dumps(updated))
    expected = updated_resp.json()

    assert updated == expected


def test_filters(site, client):
    """Test cidr/address/prefix/attribute filters for Networks."""

    # URIs
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the Network objects and retreive them for testing.
    client.post(net_uri, data=load('networks.json'))
    net_resp = client.retrieve(net_uri)
    networks = get_result(net_resp)

    # Test lookup by cidr
    wanted = ['10.0.0.0/8']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, cidr='10.0.0.0/8'),
        expected
    )

    # Test lookup by attributes
    wanted = ['192.168.0.0/16', '172.16.0.0/12']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, attributes='foo=baz'),
        expected
    )

    # Test lookup with multiple attributes
    wanted = ['172.16.0.0/12']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, attributes=['foo=baz', 'cluster=lax']),
        expected
    )

    # Test lookup by network_address
    wanted = ['169.254.0.0/16']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, network_address='169.254.0.0'),
        expected
    )

    # Test lookup by prefix_length
    wanted = ['192.168.0.0/16', '169.254.0.0/16']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, prefix_length=16),
        expected
    )

    # Test lookup by network_address + prefix_length
    wanted = ['10.0.0.0/8']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, network_address='10.0.0.0', prefix_length=8),
        expected
    )

    # Test include_ips=True, include_networks=False
    wanted = ['192.168.0.1/32']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, include_ips=True, include_networks=False),
        expected
    )

    # Test include_ips=False, include_networks=True
    wanted = ['192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12',
              '169.254.0.0/16', '192.168.0.0/24', '192.168.0.0/25']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, include_ips=False, include_networks=True),
        expected
    )

    # Test include_ips=True, include_networks=True
    wanted = ['192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12',
              '169.254.0.0/16', '192.168.0.1/32', '192.168.0.0/24',
              '192.168.0.0/25']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, include_ips=True, include_networks=True),
        expected
    )

    # Test include_ips=False, include_networks=False
    wanted = []
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(net_uri, include_ips=False, include_networks=False),
        expected
    )

    # Test lookup by ip_version (against ipv6)
    ipv6_resp = client.create(net_uri, cidr='2401:d:d0e::/64')
    ipv6 = get_result(ipv6_resp)
    wanted = ['2401:d:d0e::/64']
    expected = [ipv6]
    assert_success(
        client.retrieve(net_uri, ip_version='6'),
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
    net_resp = client.retrieve(net_uri)
    networks = get_result(net_resp)

    # INTERSECTION: foo=bar
    wanted = ['10.0.0.0/8', '169.254.0.0/16']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(query_uri, query='foo=bar'),
        expected
    )

    # INTERSECTION: foo=bar owner=jathan
    wanted = ['169.254.0.0/16']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(query_uri, query='foo=bar owner=jathan'),
        expected
    )

    # DIFFERENCE: -owner=gary, networks only
    wanted = ['192.168.0.0/16', '169.254.0.0/16', '192.168.0.0/24',
              '192.168.0.0/25']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(query_uri, query='-owner=gary', include_ips=False),
        expected
    )

    # UNION: cluster +foo=baz
    wanted = ['192.168.0.0/16', '172.16.0.0/12']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(query_uri, query='cluster +foo=baz'),
        expected
    )

    # Single IP result.
    wanted = ['192.168.0.1/32']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(query_uri, query='vlan=300'),
        expected
    )

    # UNIQUE: hostname=foo-bar1 vlan=300
    wanted = ['192.168.0.1/32']
    expected = filter_networks(networks, wanted)
    assert_success(
        client.retrieve(query_uri, query='hostname=foo-bar1 vlan=300', unique=True),
        expected
    )

    # ERROR: not unique
    assert_error(
        client.retrieve(query_uri, query='cluster +foo=baz', unique=True),
        status.HTTP_400_BAD_REQUEST
    )

    # ERROR: no results
    assert_error(
        client.retrieve(query_uri, query='cluster owner=bob', unique=True),
        status.HTTP_400_BAD_REQUEST
    )

    # ERROR: bad query
    assert_error(
        client.retrieve(query_uri, query='fake=bad'),
        status.HTTP_400_BAD_REQUEST
    )


def test_update(live_server, user, site):
    """Test updating Networks by pk and natural_key."""
    admin_client = Client(live_server, 'admin')
    user_client = Client(live_server, 'user')
    cidr = '10.0.0.0/24'

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    admin_client.create(attr_uri, resource_name='Network', name='attr1')
    net_resp = admin_client.create(
        net_uri, cidr=cidr, attributes={'attr1': 'foo'},
        state='reserved'
    )

    # Extract the Network object so that we can play w/ it during update tests.
    net = get_result(net_resp)
    net_obj_uri = site.detail_uri('network', id=net['id'])

    # Empty attributes should only clear attributes. Change state to 'allocatd'
    params = {'attributes': {}, 'state': 'allocated'}
    net.update(params)

    assert_success(
        admin_client.update(net_obj_uri, **params),
        net
    )

    # Now put attributes back
    params['attributes'] = {'attr1': 'foo'}
    net.update(params)

    assert_success(
        admin_client.update(net_obj_uri, **params),
        net
    )

    # Invalid permissions
    assert_error(user_client.update(net_obj_uri), status.HTTP_403_FORBIDDEN)

    # Test update by natural_key by zeroing out the attribtues again.
    params = {'attributes': {}, 'state': 'orphaned'}
    net.update(params)

    net_natural_uri = site.detail_uri('network', id=cidr)
    assert_success(
        admin_client.update(net_natural_uri, **params),
        net
    )


def test_partial_update(site, client):
    """"Test PATCH operations to partially update a Network."""
    net_uri = site.list_uri('network')
    attr_uri = site.list_uri('attribute')
    cidr = '10.0.0.0/24'

    client.create(attr_uri, resource_name='Network', name='attr1')
    net_resp = client.create(
        net_uri, cidr=cidr, attributes={'attr1': 'foo'}
    )

    # Extract the Network object so that we can play w/ it during update tests.
    net = get_result(net_resp)
    net_pk_uri = site.detail_uri('network', id=net['id'])
    net_natural_uri = site.detail_uri('network', id=cidr)

    # Now PATCH it by providing *only* the state, which wouldn't be
    # possible in a PUT.
    params = {'state': 'reserved'}
    net.update(params)

    assert_success(
        client.partial_update(net_pk_uri, **params),
        net
    )

    # And just to make sure a PUT with the same payload fails...
    assert_error(
        client.update(net_pk_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )


def test_deletion(site, client):
    """Test deletion of Networks."""
    net_uri = site.list_uri('network')
    attr_uri = site.list_uri('attribute')

    net1_resp = client.create(net_uri, cidr='10.0.0.0/24')
    net1 = get_result(net1_resp)
    net1_obj_uri = site.detail_uri('network', id=net1['id'])

    net2_resp = client.create(net_uri, cidr='10.0.0.1/32')
    net2 = get_result(net2_resp)
    net2_obj_uri = site.detail_uri('network', id=net2['id'])

    # Don't allow delete when there's an attached subnet/ip
    assert_error(client.delete(net1_obj_uri), 
        status.HTTP_409_CONFLICT)

    # Delete the child Network
    client.delete(net2_obj_uri)

    # And safely delete the parent Network
    assert_deleted(client.delete(net1_obj_uri))

    # Create Network 3 and delete it by natural_key
    net3_resp = client.create(net_uri, cidr='10.0.0.0/8')
    net3 = get_result(net3_resp)
    net3_natural_uri = site.detail_uri('network', id=mkcidr(net3))
    assert_deleted(client.delete(net3_natural_uri))


def test_force_deletion(site, client):
    """Test forceful deletion of Networks and proper reparenting."""

    net_uri = site.list_uri('network')
    slash23 = '10.45.10.0/23'
    slash32 = '10.45.10.1/32'
    slash24 = '10.45.10.0/24'

    # /23
    net1_resp = client.create(net_uri, cidr=slash23)
    net1 = get_result(net1_resp)
    net1_obj_uri = site.detail_uri('network', id=net1['id'])

    # /32
    net2_resp = client.create(net_uri, cidr=slash32)
    net2 = get_result(net2_resp)
    net2_obj_uri = site.detail_uri('network', id=net2['id'])

    # /24
    net3_resp = client.create(net_uri, cidr=slash24)
    net3 = get_result(net3_resp)
    net3_obj_uri = site.detail_uri('network', id=net3['id'])
    """
    How this works:
        - /23 parent w/ /32 child
        - /24 created, /32 is now its child
        - /23 is now parent of /24
        - delete /24 should raise error
        - force delete /24 should succeed
        - /23 is parent of /32 again
        - delete /23 should raise an error
        - force delete /23 should raise an error.
    """
    # Delete /24 will fail, because it has a child.
    assert_error(client.destroy(net3_obj_uri),
        status.HTTP_409_CONFLICT)

    # Forcefully delete the /24
    assert_deleted(client.destroy(net3_obj_uri, force_delete=True))

    # Fetching the /32 should match the original payload
    assert_success(client.retrieve(net2_obj_uri), net2)

    # Oops, we added quad0 as a parent!
    quad0_resp = client.create(net_uri, cidr='0.0.0.0/0')
    quad0 = get_result(quad0_resp)
    quad0_obj_uri= site.detail_uri('network', id=quad0['id'])
    slash23_parent_uri = net1_obj_uri + 'parent/'

    # /0 should be parent of /23
    assert_success(client.retrieve(slash23_parent_uri), quad0)

    # Force delete quad0 and /23 parent should be null
    client.destroy(quad0_obj_uri, force_delete=True)
    assert_error(client.retrieve(slash23_parent_uri), status.HTTP_404_NOT_FOUND)

    # Force delete /23 will fail, because it has no parent and children are leaf nodes.
    assert_error(client.destroy(net1_obj_uri, force_delete=True), status.HTTP_409_CONFLICT)


def test_mptt_detail_routes(site, client):
    """Test detail routes for ancestor/children/descendants/root methods."""
    net_uri = site.list_uri('network')

    client.create(net_uri, cidr='10.0.0.0/8')
    client.create(net_uri, cidr='10.16.0.0/12')
    client.create(net_uri, cidr='10.16.0.0/14')
    client.create(net_uri, cidr='10.16.2.0/25')
    client.create(net_uri, cidr='10.16.2.1/32')
    client.create(net_uri, cidr='10.16.2.2/32')

    net_8_resp = client.retrieve(net_uri, cidr='10.0.0.0/8')
    net_8 = get_result(net_8_resp)[0]
    net_8_obj_uri = site.detail_uri('network', id=net_8['id'])

    net_12_resp = client.retrieve(net_uri, cidr='10.16.0.0/12')
    net_12 = get_result(net_12_resp)[0]
    net_12_obj_uri = site.detail_uri('network', id=net_12['id'])

    net_14_resp = client.retrieve(net_uri, cidr='10.16.0.0/14')
    net_14 = get_result(net_14_resp)[0]
    net_14_obj_uri = site.detail_uri('network', id=net_14['id'])

    net_25_resp = client.retrieve(net_uri, cidr='10.16.2.0/25')
    net_25 = get_result(net_25_resp)[0]
    net_25_obj_uri = site.detail_uri('network', id=net_25['id'])

    ip1_resp = client.retrieve(net_uri, cidr='10.16.2.1/32')
    ip1 = get_result(ip1_resp)[0]
    ip1_obj_uri = site.detail_uri('network', id=ip1['id'])

    ip2_resp = client.retrieve(net_uri, cidr='10.16.2.2/32')
    ip2 = get_result(ip2_resp)[0]
    ip2_obj_uri = site.detail_uri('network', id=ip2['id'])

    # ancestors
    expected = [net_8, net_12, net_14]
    uri = reverse('network-ancestors', args=(site.id, net_25['id']))
    natural_uri = reverse('network-ancestors', args=(site.id, mkcidr(net_25)))
    assert_success(client.retrieve(uri), expected)

    expected = [net_14, net_12, net_8]
    assert_success(client.retrieve(uri, ascending=True), expected)
    assert_success(client.retrieve(natural_uri, ascending=True), expected)

    # children
    uri = reverse('network-children', args=(site.id, net_25['id']))
    natural_uri = reverse('network-children', args=(site.id, mkcidr(net_25)))
    wanted = [ip1, ip2]
    expected = wanted
    assert_success(client.retrieve(uri), expected)
    assert_success(client.retrieve(natural_uri), expected)

    uri = reverse('network-children', args=(site.id, net_12['id']))
    natural_uri = reverse('network-children', args=(site.id, mkcidr(net_12)))
    wanted = [net_14]
    expected = wanted
    assert_success(client.retrieve(uri), expected)
    assert_success(client.retrieve(natural_uri), expected)

    # descendants (spelled correctly)
    uri = reverse('network-descendants', args=(site.id, net_8['id']))
    natural_uri = reverse('network-descendants', args=(site.id, mkcidr(net_8)))
    wanted = [net_12, net_14, net_25, ip1, ip2]
    expected = wanted
    assert_success(client.retrieve(uri), expected)
    assert_success(client.retrieve(natural_uri), expected)

    uri = reverse('network-descendants', args=(site.id, net_14['id']))
    natural_uri = reverse(
        'network-descendants', args=(site.id, mkcidr(net_14))
    )
    wanted = [net_25, ip1, ip2]
    expected = wanted
    assert_success(client.retrieve(uri), expected)
    assert_success(client.retrieve(natural_uri), expected)

    uri = reverse('network-descendants', args=(site.id, ip2['id']))
    natural_uri = reverse('network-descendants', args=(site.id, mkcidr(ip2)))
    expected = []
    assert_success(client.retrieve(uri), expected)
    assert_success(client.retrieve(natural_uri), expected)

    # descendents (spelled incorrectly) should send along a "Warning" header
    # TODO(jathan): This should be removed no earlier than v1.3 release.
    uri = reverse('network-descendents', args=(site.id, net_14['id']))
    expected = [net_25, ip1, ip2]
    response = client.retrieve(uri)
    assert_success(response, expected)
    assert response.headers.get('Warning') is not None

    # parent
    uri = reverse('network-parent', args=(site.id, ip2['id']))
    natural_uri = reverse('network-parent', args=(site.id, mkcidr(ip2)))
    assert_success(client.retrieve(uri), net_25)
    assert_success(client.retrieve(natural_uri), net_25)

    # root
    uri = reverse('network-root', args=(site.id, ip1['id']))
    natural_uri = reverse('network-root', args=(site.id, mkcidr(ip1)))
    assert_success(client.retrieve(uri), net_8)
    assert_success(client.retrieve(natural_uri), net_8)

    uri = reverse('network-root', args=(site.id, net_8['id']))
    natural_uri = reverse('network-root', args=(site.id, mkcidr(net_8)))
    assert_error(client.retrieve(uri), status.HTTP_404_NOT_FOUND)
    assert_error(client.retrieve(natural_uri), status.HTTP_404_NOT_FOUND)

    # siblings
    uri = reverse('network-siblings', args=(site.id, ip1['id']))
    natural_uri = reverse('network-siblings', args=(site.id, mkcidr(ip1)))
    wanted = [ip2]
    expected = wanted
    assert_success(client.retrieve(uri), expected)
    assert_success(client.retrieve(natural_uri), expected)

    wanted = [ip1, ip2]
    expected = wanted
    assert_success(client.retrieve(uri, include_self=True), expected)
    assert_success(client.retrieve(natural_uri, include_self=True), expected)


def test_get_next_detail_routes(site, client):
    """Test the detail routes for getting next available networks/addresses."""
    net_uri = site.list_uri('network')

    client.create(net_uri, cidr='10.16.2.0/25')
    client.create(net_uri, cidr='10.16.2.8/29')
    client.create(net_uri, cidr='10.16.2.1/32')
    client.create(net_uri, cidr='10.16.2.2/32')
    client.create(net_uri, cidr='10.16.2.4/32')
    client.create(net_uri, cidr='10.16.2.17/32')

    net_25_resp = client.retrieve(net_uri, cidr='10.16.2.0/25')
    net_25 = get_result(net_25_resp)[0]
    net_25_obj_uri = site.detail_uri('network', id=net_25['id'])

    net_29_resp = client.retrieve(net_uri, cidr='10.16.2.8/29')
    net_29 = get_result(net_29_resp)[0]
    net_29_obj_uri = site.detail_uri('network', id=net_29['id'])

    ip1_resp = client.retrieve(net_uri, cidr='10.16.2.1/32')
    ip1 = get_result(ip1_resp)[0]
    ip1_obj_uri = site.detail_uri('network', id=ip1['id'])

    ip2_resp = client.retrieve(net_uri, cidr='10.16.2.2/32')
    ip2 = get_result(ip2_resp)[0]
    ip2_obj_uri = site.detail_uri('network', id=ip2['id'])

    ip3_resp = client.retrieve(net_uri, cidr='10.16.2.2/32')
    ip3 = get_result(ip3_resp)[0]
    ip3_obj_uri = site.detail_uri('network', id=ip3['id'])

    #
    # next_network
    #
    uri = reverse('network-next-network', args=(site.id, net_25['id']))
    natural_uri = reverse(
        'network-next-network', args=(site.id, mkcidr(net_25))
    )

    # A single /28
    expected = [u'10.16.2.32/28']
    assert_success(client.retrieve(uri, prefix_length=28), expected)
    assert_success(client.retrieve(natural_uri, prefix_length=28), expected)

    # 3x remaining /27 in the /25
    networks = [u'10.16.2.32/27', u'10.16.2.64/27', u'10.16.2.96/27']
    assert_success(
        client.retrieve(uri, prefix_length=27, num=3),
        networks
    )
    assert_success(
        client.retrieve(natural_uri, prefix_length=27, num=3),
        networks
    )

    # Missing/invalid prefix_length
    ## by pk
    assert_error(client.retrieve(uri), status.HTTP_400_BAD_REQUEST)
    assert_error(client.retrieve(uri, prefix_length='ralph'), status.HTTP_400_BAD_REQUEST)
    assert_error(client.retrieve(uri, prefix_length=14), status.HTTP_400_BAD_REQUEST)
    assert_error(client.retrieve(uri, prefix_length=65), status.HTTP_400_BAD_REQUEST)

    ## by natural_key
    assert_error(client.retrieve(natural_uri), status.HTTP_400_BAD_REQUEST)
    assert_error(
        client.retrieve(natural_uri, prefix_length='ralph'),
        status.HTTP_400_BAD_REQUEST
    )
    assert_error(
        client.retrieve(natural_uri, prefix_length=14),
        status.HTTP_400_BAD_REQUEST
    )
    assert_error(
        client.retrieve(natural_uri, prefix_length=65), status.HTTP_400_BAD_REQUEST
    )

    # Invalid num
    assert_error(
        client.retrieve(uri, prefix_length=28, num='potato'),
        status.HTTP_400_BAD_REQUEST
    )

    #
    # next_address
    #
    uri = reverse('network-next-address', args=(site.id, net_25['id']))
    natural_uri = reverse(
        'network-next-address', args=(site.id, mkcidr(net_25))
    )

    # A single /32
    assert_success(client.retrieve(uri), [u'10.16.2.3/32'])
    assert_success(client.retrieve(natural_uri), [u'10.16.2.3/32'])

    # 3x /32
    addresses = [u'10.16.2.3/32', u'10.16.2.5/32', u'10.16.2.6/32']
    assert_success(client.retrieve(uri, num=3), addresses)
    assert_success(client.retrieve(natural_uri, num=3), addresses)

    # Invalid num is all we can really test for.
    assert_error(
        client.retrieve(uri, num='potato'),
        status.HTTP_400_BAD_REQUEST
    )
    assert_error(
        client.retrieve(natural_uri, num='potato'),
        status.HTTP_400_BAD_REQUEST
    )


def test_next_network_allocation(site, client):
    net_uri = site.list_uri('network')

    client.create(net_uri, cidr='10.1.2.0/24')

    net_24_resp = client.retrieve(net_uri, cidr='10.1.2.0/24')
    net_24 = get_result(net_24_resp)[0]
    net_24_obj_uri = site.detail_uri('network', id=net_24['id'])

    uri = reverse('network-next-network', args=(site.id, net_24['id']))

    client.post(uri, params={u'prefix_length': u'32'})
    assert_success(client.retrieve(uri, prefix_length=32), [u'10.1.2.2/32'])

    client.post(uri, params={u'prefix_length': u'32', u'reserve': u'True'})

    uri = reverse('network-reserved', args=(site.id,))
    assert get_result(client.retrieve(uri))[0]['network_address'] == u'10.1.2.2'


def test_next_address_allocation(site, client):
    net_uri = site.list_uri('network')

    client.create(net_uri, cidr='10.1.2.0/24')

    net_24_resp = client.retrieve(net_uri, cidr='10.1.2.0/24')
    net_24 = get_result(net_24_resp)[0]
    net_24_obj_uri = site.detail_uri('network', id=net_24['id'])

    uri = reverse('network-next-address', args=(site.id, net_24['id']))

    client.post(uri)
    assert_success(client.retrieve(uri, prefix_length=32), [u'10.1.2.2/32'])

    client.post(uri, params={u'reserve': u'True'})

    uri = reverse('network-reserved', args=(site.id,))
    assert get_result(client.retrieve(uri))[0]['network_address'] == u'10.1.2.2'


def test_reservation_list_route(site, client):
    """Test the list route for getting reserved networks/addresses."""
    net_uri = site.list_uri('network')
    res_uri = reverse('network-reserved', args=(site.id,))

    net_resp = client.create(net_uri, cidr='192.168.3.0/24', state='reserved')
    net = get_result(net_resp)

    # Fetch the reserved networks and make sure they match up.
    networks = [net]
    expected = networks
    assert_success(client.retrieve(res_uri), expected)


def test_closest_parent_detail_route(site, client):
    """
    Test the detail route for looking up the closest parent for a
    Network.

    GET /api/sites/1/networks/10.250.0.1/32/closest_parent/
    """
    net_uri = site.list_uri('network')

    # Create networks
    root_resp = client.create(net_uri, cidr='10.250.0.0/16')
    root = get_result(root_resp)
    parent_resp = client.create(net_uri, cidr='10.250.0.0/24')
    parent = get_result(parent_resp)

    # To make sure that a /25 doesn't return as closest parent. See: issue #209
    client.create(net_uri, cidr='10.250.0.0/25')

    # Closest parent for non-existent /32 should be ``parent``
    closest_uri = reverse(
        'network-closest-parent', args=(site.id, '10.250.0.185/32')
    )
    expected = parent
    assert_success(client.retrieve(closest_uri), expected)

    # Matching ip with shorter prefix_length should 404
    assert_error(
        client.retrieve(closest_uri, prefix_length=27),
        status.HTTP_404_NOT_FOUND
    )

    # Invalid prefix_length should 400
    assert_error(
        client.retrieve(closest_uri, prefix_length='shoe'),
        status.HTTP_400_BAD_REQUEST
    )

    # Invalid cidr should 400
    bad_closest_uri = reverse(
        'network-closest-parent', args=(site.id, 1)
    )
    assert_error(client.retrieve(bad_closest_uri), status.HTTP_400_BAD_REQUEST)

    # Alpha cidr should 404
    abc_closest_uri = reverse(
        'network-closest-parent', args=(site.id, 'bogus')
    )
    assert_error(client.retrieve(abc_closest_uri), status.HTTP_404_NOT_FOUND)

    # If a closest parent isn't found it should 404
    no_closest_uri = reverse(
        'network-closest-parent', args=(site.id, '1.0.0.1/32')
    )
    assert_error(client.retrieve(no_closest_uri), status.HTTP_404_NOT_FOUND)
