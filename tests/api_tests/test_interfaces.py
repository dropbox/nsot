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
    Client, load, filter_interfaces
)


log = logging.getLogger(__name__)


def test_creation(site, client):
    """Test basic creation of an Interface."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = dev_resp.json()['data']['device']

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = net_resp.json()['data']['network']

    # Missing required field (device, name)
    assert_error(
        client.create(ifc_uri, attributes={'attr1': 'foo'}),
        status.HTTP_400_BAD_REQUEST
    )

    # Null name
    assert_error(
        client.create(ifc_uri, device=dev['id'], name=None),
        status.HTTP_400_BAD_REQUEST
    )

    # Verify successful creation
    ifc_resp = client.create(ifc_uri, device=dev['id'], name='eth0')
    ifc = ifc_resp.json()['data']['interface']
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    assert_created(ifc_resp, ifc_obj_uri)

    # Verify successful retrieval of all Interfaces
    expected = ifc_resp.json()['data']
    expected['interfaces'] = [expected.pop('interface')]
    expected.update({'limit': None, 'offset': 0, 'total': 1})

    assert_success(client.get(ifc_uri), expected)

    # Verify successful get of single Interface
    assert_success(client.get(ifc_obj_uri), {'interface': ifc})


def test_creation_with_addresses(site, client):
    """Test creating an Interface w/ addresses."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = dev_resp.json()['data']['device']

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = net_resp.json()['data']['network']

    addresses = ['10.1.1.1/32', '10.1.1.2/32', '10.1.1.3/32']

    # Create an Interface w/ addresses up front.
    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=addresses
    )
    ifc = ifc_resp.json()['data']['interface']
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Verify successful creation
    assert_created(ifc_resp, ifc_obj_uri)

    # Verify successful retrieval of the Interface
    expected = ifc_resp.json()['data']
    expected['interfaces'] = [expected.pop('interface')]
    expected.update({'limit': None, 'offset': 0, 'total': 1})

    assert_success(client.get(ifc_uri), expected)

    # Verify successful get of single Interface
    assert_success(client.get(ifc_obj_uri), {'interface': ifc})


def test_collection_creation(site, client):
    """Test creating multiple Interfaces at once."""
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = dev_resp.json()['data']['device']

    # Successfully create a collection of Interfaces
    collection = [
        {'device': dev['id'], 'name': 'foo1'},
        {'device': dev['id'], 'name': 'foo2'},
        {'device': dev['id'], 'name': 'foo3'},
    ]
    collection_response = client.post(
        ifc_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Networks
    output = collection_response.json()
    output['data'].update({
        'limit': None, 'offset': 0, 'total': len(collection)
    })

    assert_success(client.get(ifc_uri), output['data'])


def test_update(site, client):
    """Test update of an existing interface w/ an address."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = dev_resp.json()['data']['device']

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = net_resp.json()['data']['network']

    # Create eth0 w/ an address
    addresses = ['10.1.1.1/32']
    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=addresses
    )
    ifc = ifc_resp.json()['data']['interface']
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Create eth1 w/ no address
    ifc2_resp = client.create(ifc_uri, device=dev['id'], name='eth1')
    ifc2 = ifc2_resp.json()['data']['interface']
    ifc2_obj_uri = site.detail_uri('interface', id=ifc2['id'])

    # Assigning eth0's address to eth1 should fail.
    params = ifc2.copy()
    params['addresses'] = addresses
    assert_error(
        client.update(ifc2_obj_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )

    # (device_id, name) must be unique
    params['name'] = 'eth0'
    assert_error(
        client.update(ifc2_obj_uri, **params),
        status.HTTP_409_CONFLICT
    )

    # Test zeroing out addresses on the Interface
    params['name'] = 'eth1'
    params['addresses'] = []
    ifc2.update(params)
    assert_success(
        client.update(ifc2_obj_uri, **params),
        {'interface': ifc2}
    )


def test_filters(site, client):
    """Test field filters for Interfaces."""
    ifc_uri = site.list_uri('interface')
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev1_resp = client.create(dev_uri, hostname='foo-bar1')
    dev2_resp = client.create(dev_uri, hostname='foo-bar2')

    dev1 = dev1_resp.json()['data']['device']
    dev2 = dev2_resp.json()['data']['device']

    # Create Interfaces
    dev1_eth0_resp = client.create(ifc_uri, device=dev1['id'], name='eth0')
    dev1_eth0 = dev1_eth0_resp.json()['data']['interface']

    dev1_eth1_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth1', speed=40000, type=161
    )
    dev1_eth1 = dev1_eth1_resp.json()['data']['interface']

    dev2_eth0_resp = client.create(
        ifc_uri, device=dev2['id'], name='eth0', description='foo-bar2:eth0'
    )
    dev2_eth0 = dev2_eth0_resp.json()['data']['interface']

    dev2_eth1_resp = client.create(
        ifc_uri, device=dev2['id'], name='eth1', type=161,
        parent=dev2_eth0['id']
    )
    dev2_eth1 = dev2_eth1_resp.json()['data']['interface']


    # Populate the Interface objects and retreive them for testing.
    interfaces_resp = client.get(ifc_uri)
    interfaces_out = interfaces_resp.json()['data']
    interfaces = interfaces_out['interfaces']

    # Test filter by name
    expected = copy.deepcopy(interfaces_out)
    wanted = [dev1_eth0, dev2_eth0]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(ifc_uri, name='eth0'),
        expected
    )

    # Test filter by device_id
    wanted = [dev1_eth0, dev1_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(ifc_uri, device_id=dev1['id']),
        expected
    )

    # Test filter by speed
    wanted = [dev1_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(ifc_uri, speed=40000),
        expected
    )

    # Test filter by type
    wanted = [dev1_eth1, dev2_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(ifc_uri, type=161),
        expected
    )

    # Test filter by description
    wanted = [dev2_eth0]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(ifc_uri, description='foo-bar2:eth0'),
        expected
    )

    # Test filter by parent_id
    wanted = [dev2_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(ifc_uri, parent_id=dev2_eth0['id']),
        expected
    )


def test_set_queries(client, site):
    """Test set queries for Interfaces."""
    # URIs
    dev_uri = site.list_uri('device')
    attr_uri = site.list_uri('attribute')
    ifc_uri = site.list_uri('interface')
    query_uri = site.query_uri('interface')

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Create Devices
    dev1_resp = client.create(dev_uri, hostname='foo-bar1')
    dev2_resp = client.create(dev_uri, hostname='foo-bar2')

    dev1 = dev1_resp.json()['data']['device']
    dev2 = dev2_resp.json()['data']['device']

    # Create Interfaces
    dev1_eth0_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth0',
        attributes={'vlan': '300', 'scope': 'region'},
    )
    dev1_eth1_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth1',
        attributes={'vlan': '300', 'scope': 'global'},
    )
    dev2_eth0_resp = client.create(
        ifc_uri, device=dev2['id'], name='eth0',
        attributes={'scope': 'region'},
    )
    dev2_eth1_resp = client.create(
        ifc_uri, device=dev2['id'], name='eth1',
        attributes={'vlan': '400', 'scope': 'metro'},
    )

    dev1_eth0 = dev1_eth0_resp.json()['data']['interface']
    dev1_eth1 = dev1_eth1_resp.json()['data']['interface']
    dev2_eth0 = dev2_eth0_resp.json()['data']['interface']
    dev2_eth1 = dev2_eth1_resp.json()['data']['interface']

    # Populate the Interface objects and retreive them for testing.
    interfaces_resp = client.get(ifc_uri)
    interfaces_out = interfaces_resp.json()['data']
    interfaces = interfaces_out['interfaces']

    # INTERSECTION: vlan=300
    expected = copy.deepcopy(interfaces_out)
    wanted = [dev1_eth0, dev1_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='vlan=300'),
        expected
    )

    # INTERSECTION: vlan=300 scope=region
    wanted = [dev1_eth0]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='vlan=300 scope=region'),
        expected
    )

    # DIFFERENCE: -scope=region
    wanted = [dev1_eth1, dev2_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='-scope=region'),
        expected
    )

    # UNION: scope=global +vlan=400
    wanted = [dev1_eth1, dev2_eth1]
    expected['interfaces'] = filter_interfaces(interfaces, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='scope=global +vlan=400'),
        expected
    )


def test_deletion(site, client):
    """Test deletion of Interfaces."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')

    dev1_resp = client.create(dev_uri, hostname='foo-bar1')
    dev1 = dev1_resp.json()['data']['device']

    # Create Interfaces
    dev1_eth0_resp = client.create(ifc_uri, device=dev1['id'], name='eth0')
    dev1_eth0 = dev1_eth0_resp.json()['data']['interface']
    dev1_eth0_uri = site.detail_uri('interface', id=dev1_eth0['id'])

    dev1_eth1_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth1', parent=dev1_eth0['id']
    )
    dev1_eth1 = dev1_eth1_resp.json()['data']['interface']
    dev1_eth1_uri = site.detail_uri('interface', id=dev1_eth1['id'])

    # Don't allow delete when there's a child Interface
    assert_error(client.delete(dev1_eth0_uri), status.HTTP_409_CONFLICT)

    # Delete the child Interface
    client.delete(dev1_eth1_uri)

    # And safely delete the parent Network
    assert_deleted(client.delete(dev1_eth0_uri))


def test_detail_routes(site, client):

    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = dev_resp.json()['data']['device']

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = net_resp.json()['data']['network']

    set_addresses = ['10.1.1.1/32', '10.1.1.2/32', '10.1.1.3/32']

    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=set_addresses
    )
    ifc = ifc_resp.json()['data']['interface']
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Fetch the Network address objects
    addresses_resp = client.retrieve(
        net_uri, include_ips=True, include_networks=False
    )
    addresses_out = addresses_resp.json()['data']
    addresses = addresses_out['networks']

    # Verify Interface.addresses
    addresses_uri = reverse('interface-addresses', args=(site.id, ifc['id']))
    expected = {
        'total': len(addresses),
        'limit': None,
        'offset': 0,
        'addresses': addresses,
    }
    assert_success(client.retrieve(addresses_uri), expected)

    # Verify Interface.networks
    networks_uri = reverse('interface-networks', args=(site.id, ifc['id']))
    networks = [net]
    expected.pop('addresses')  # We don't want addresess here.
    expected.update({'networks': networks, 'total': len(networks)})
    assert_success(client.retrieve(networks_uri), expected)

    # Verify assignments
    # FIXME(jathan): Assignments detail route testing is NYI!
