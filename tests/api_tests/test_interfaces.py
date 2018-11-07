# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import copy
from django.conf import settings
from django.core.urlresolvers import reverse
import json
import logging
from rest_framework import status

from nsot.util import slugify, slugify_interface

from .fixtures import live_server, client, user, site, user_client
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, load, filter_interfaces, get_result
)


log = logging.getLogger(__name__)


@pytest.fixture
def device(site, client):
    dev_uri = site.list_uri('device')
    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    return dev


def test_creation(site, client):
    """Test basic creation of an Interface."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    dev_resp1 = client.create(dev_uri, hostname='foo-bar2')
    dev1 = get_result(dev_resp1)

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = get_result(net_resp)

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

    # Verify successful creation w/ null MAC
    ifc1_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', parent_id=None,
        mac_address=None,
    )
    ifc1 = get_result(ifc1_resp)
    ifc1_obj_uri = site.detail_uri('interface', id=ifc1['id'])

    assert_created(ifc1_resp, ifc1_obj_uri)

    # Verify that creating a device with parent as
    # ifc1 but device as foo-bar2 will cause error
    assert_error(
        client.create(ifc_uri, device=dev1['id'], name='eth0.1', parent_id=ifc1['id']),
        status.HTTP_400_BAD_REQUEST
    )

    # Make sure MAC is None
    assert ifc1['mac_address'] is None

    # Create another interface with ifc1 as parent, w/ 0 MAC
    ifc2_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0.0', parent_id=ifc1['id'],
        mac_address=0
    )
    ifc2 = get_result(ifc2_resp)
    ifc2_obj_uri = site.detail_uri('interface', id=ifc2['id'])

    assert_created(ifc2_resp, ifc2_obj_uri)

    # Create yet another interface using Device hostname
    ifc3_resp = client.create(ifc_uri, device=dev['hostname'], name='eth1.0')
    ifc3 = get_result(ifc3_resp)
    ifc3_obj_uri = site.detail_uri('interface', id=ifc3['id'])

    assert_created(ifc3_resp, ifc3_obj_uri)

    # Create an interface using Device hostname with parent_id specified by natural
    # key (!!)
    ifc4_resp = client.create(
        ifc_uri, device=dev['hostname'], name='eth1.1',
        parent_id=ifc3['name_slug']
    )
    ifc4 = get_result(ifc4_resp)
    ifc4_obj_uri = site.detail_uri('interface', id=ifc4['id'])

    assert_created(ifc4_resp, ifc4_obj_uri)

    # Verify successful get of single Interface
    assert_success(client.get(ifc1_obj_uri), ifc1)

    # Verify successful get of single Interface by natural key
    natural_key = slugify_interface(**ifc1)
    ifc1_natural_uri = site.detail_uri('interface', id=natural_key)
    assert_success(client.get(ifc1_natural_uri), ifc1)

    # Verify successful retrieval of all Interfaces
    interfaces = [ifc1, ifc2, ifc3, ifc4]
    expected = interfaces
    assert_success(client.get(ifc_uri), expected)


def test_creation_speed(site, client, device):
    """
    Test the behavior of the ``speed`` field with creation
    """
    ifc_uri = site.list_uri('interface')

    # Default, with speed omitted from request
    response = client.create(ifc_uri, device=device['id'], name='eth1')
    ifc = get_result(response)
    assert ifc['speed'] == settings.INTERFACE_DEFAULT_SPEED

    # Explicit speed
    response = client.create(
        ifc_uri, device=device['id'], name='eth2', speed=10000
    )
    ifc = get_result(response)
    assert ifc['speed'] == 10000

    # Speed set to None, should come back as None and not the default
    response = client.create(
        ifc_uri, device=device['id'], name='eth3', speed=None
    )
    ifc = get_result(response)
    assert ifc['speed'] is None


def test_tree_traversal(site, client):
    """Test basic creation of an Interface."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    dev_resp1 = client.create(dev_uri, hostname='foo-bar2')
    dev1 = get_result(dev_resp1)

    ifc1_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', parent_id=None,
        mac_address=None,
    )
    ifc1 = get_result(ifc1_resp)
    ifc1_obj_uri = site.detail_uri('interface', id=ifc1['id'])

    assert_created(ifc1_resp, ifc1_obj_uri)

    # Create another interface with ifc1 as parent
    ifc2_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0.0', parent_id=ifc1['id'],
        mac_address=None
    )
    ifc2 = get_result(ifc2_resp)
    ifc2_obj_uri = site.detail_uri('interface', id=ifc2['id'])

    assert_created(ifc2_resp, ifc2_obj_uri)

    # Create another interface with ifc2 as parent
    ifc3_resp = client.create(
        ifc_uri, device = dev['id'], name='eth0.1', parent_id=ifc2['id'],
        mac_address = None
    )
    ifc3 = get_result(ifc3_resp)
    ifc3_obj_uri = site.detail_uri('interface', id = ifc3['id'])

    assert_created(ifc3_resp, ifc3_obj_uri)

    # Create another interface with ifc2 as parent
    ifc4_resp = client.create(
        ifc_uri, device = dev['id'], name='eth0.2', parent_id=ifc2['id'],
        mac_address = None
    )
    ifc4 = get_result(ifc4_resp)
    ifc4_obj_uri = site.detail_uri('interface', id = ifc4['id'])

    assert_created(ifc4_resp, ifc4_obj_uri)

    # Create another interface with ifc2 as parent
    ifc5_resp = client.create(
        ifc_uri, device = dev['id'], name='eth0.3', parent_id=ifc2['id'],
        mac_address = None
    )

    ifc5 = get_result(ifc5_resp)
    ifc5_obj_uri = site.detail_uri('interface', id = ifc5['id'])

    assert_created(ifc5_resp, ifc5_obj_uri)

    ifc6_resp = client.create(
        ifc_uri, device = dev1['id'], name='eth0.4', parent_id=None,
        mac_address = None
    )

    ifc6 = get_result(ifc6_resp)
    ifc6_obj_uri = site.detail_uri('interface', id = ifc6['id'])

    assert_created(ifc6_resp, ifc6_obj_uri)

    ifc7_resp = client.create(
        ifc_uri, device = dev1['id'], name='eth0.5', parent_id=None,
        mac_address = None
    )

    ifc7 = get_result(ifc7_resp)
    ifc7_obj_uri = site.detail_uri('interface', id = ifc7['id'])

    assert_created(ifc7_resp, ifc7_obj_uri)

    # test Ancestors by calling it on ifc3
    expected = [ifc1, ifc2]
    uri = reverse('interface-ancestors', args = (site.id, ifc3['id']))
    assert_success(client.retrieve(uri), expected)

    # test children by calling it on ifc2
    expected = [ifc3, ifc4, ifc5]
    uri = reverse('interface-children', args = (site.id, ifc2['id']))
    assert_success(client.retrieve(uri), expected)

    # test descendants by calling it on ifc1
    expected = [ifc2, ifc3, ifc4, ifc5]
    uri = reverse('interface-descendants', args = (site.id, ifc1['id']))
    assert_success(client.retrieve(uri), expected)

    # test siblings by calling it on ifc3
    expected = [ifc4, ifc5]
    uri = reverse('interface-siblings', args = (site.id, ifc3['id']))
    assert_success(client.retrieve(uri), expected)

    # test root by calling it on ifc4
    expected = ifc1
    uri = reverse('interface-root', args=(site.id, ifc4['id']))
    assert_success(client.retrieve(uri), expected)

    # test that root of ifc1 is ifc1
    expected = ifc1
    uri = reverse('interface-root', args=(site.id, ifc1['id']))
    assert_success(client.retrieve(uri), expected)

    # test parent by calling it on ifc5
    expected = ifc2
    uri = reverse('interface-parent', args=(site.id, ifc5['id']))
    assert_success(client.retrieve(uri), expected)

    # test sibling for interfaces with None as parent and attached to different devices
    expected = [ifc7]
    uri = reverse('interface-siblings', args=(site.id, ifc6['id']))
    assert_success(client.retrieve(uri), expected)


def test_creation_with_addresses(site, client):
    """Test creating an Interface w/ addresses."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = get_result(net_resp)

    addresses = ['10.1.1.1/32', '10.1.1.2/32', '10.1.1.3/32']

    # Create an Interface w/ addresses up front.
    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=addresses
    )
    ifc = get_result(ifc_resp)
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Verify successful creation
    assert_created(ifc_resp, ifc_obj_uri)

    # Verify successful retrieval of the Interface
    payload = get_result(ifc_resp)
    expected = [payload]

    assert_success(client.get(ifc_uri), expected)

    # Verify successful get of single Interface
    assert_success(client.get(ifc_obj_uri), ifc)


def test_bulk_operations(site, client):
    """Test creating/updating multiple Interfaces at once."""
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    # Successfully create a collection of Interfaces
    collection = [
        {'device': dev['id'], 'name': 'eth1'},
        {'device': dev['id'], 'name': 'eth2'},
        {'device': dev['id'], 'name': 'eth3'},
    ]
    collection_response = client.post(
        ifc_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Interfaces
    output = collection_response.json()
    expected = get_result(output)

    assert_success(client.get(ifc_uri), expected)

    # Test update of all created Interfaces (name: eth => ae)
    updated = copy.deepcopy(expected)
    for item in updated:
        item['name'] = item['name'].replace('eth', 'ae')
        item['name_slug'] = item['name_slug'].replace('eth', 'ae')
    updated_resp = client.put(ifc_uri, data=json.dumps(updated))
    expected = updated_resp.json()

    assert updated == expected


def test_update(site, client):
    """Test update of an existing interface w/ an address."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = get_result(net_resp)

    # Create eth0 w/ an address
    addresses = ['10.1.1.1/32']
    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=addresses
    )
    ifc = get_result(ifc_resp)
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Create eth1 w/ no address
    ifc2_resp = client.create(ifc_uri, device=dev['id'], name='eth1')
    ifc2 = get_result(ifc2_resp)
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
        ifc2
    )

    # Assign addresses by natural key
    natural_key = slugify_interface(**ifc2)
    ifc2_natural_uri = site.detail_uri('interface', id=natural_key)
    params['name'] = 'eth3'
    payload = copy.deepcopy(params)
    payload['name_slug'] = slugify_interface(**payload)

    assert_success(
        client.update(ifc2_natural_uri, **params),
        payload
    )

    # Update parent by natural key (set `ifc` as parent to `ifc2`)
    params['parent_id'] = ifc['name_slug']
    payload['parent_id'] = ifc['id']
    payload['parent'] = ifc['name_slug']
    payload['name_slug'] = slugify_interface(**payload)

    assert_success(
        client.update(ifc2_obj_uri, **params),
        payload
    )


def test_partial_update(site, client):
    """Test PATCH operations to partially update an Interface."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')
    attr_uri = site.list_uri('attribute')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = get_result(net_resp)

    client.create(attr_uri, name='attr1', resource_name='Interface')

    # Create eth0 w/ an address
    addresses = ['10.1.1.1/32']
    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=addresses,
        attributes={'attr1': 'value'}

    )
    ifc = get_result(ifc_resp)
    ifc_pk_uri = site.detail_uri('interface', id=ifc['id'])

    # Assert that a partial update on PUT will fail
    params = {'name': 'ge-0/0/1'}
    assert_error(
        client.update(ifc_pk_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )

    # Update only name
    payload = copy.deepcopy(ifc)
    params = {'name': 'ge-0/0/1'}
    payload.update(params)
    payload['name_slug'] = slugify_interface(**payload)
    assert_success(
        client.partial_update(ifc_pk_uri, **params),
        payload
    )

    # Update only attributes
    params = {'attributes': {}}  # Nuke 'em
    payload.update(params)
    assert_success(
        client.partial_update(ifc_pk_uri, **params),
        payload
    )

    # Update attributes by natural key
    natural_key = slugify_interface(**payload)
    ifc_natural_uri = site.detail_uri('interface', id=natural_key)
    params = {'attributes': {'attr1': 'bar'}}
    payload.update(params)
    assert_success(
        client.partial_update(ifc_natural_uri, **params),
        payload
    )

    # Update name and confirm natural key change
    params = {'name': 'xe-1/2/3:10.0'}
    payload.update(params)
    payload['name_slug'] = slugify_interface(**payload)
    assert_success(
        client.partial_update(ifc_natural_uri, **params),
        payload
    )
    # Old natural key URI should fail
    assert_error(client.get(ifc_natural_uri), status.HTTP_404_NOT_FOUND)
    # Build new natural key
    natural_key = slugify_interface(**payload)
    ifc_natural_uri = site.detail_uri('interface', id=natural_key)
    # Confirm new URI works
    assert_success(client.get(ifc_natural_uri), payload)

    # Update only addresses
    params = {'addresses': ['10.1.1.2/32']}
    payload.update(params)
    assert_success(
        client.partial_update(ifc_pk_uri, **params),
        payload
    )

    # Nuke addresses
    params = {'addresses': []}  # Nuke 'em!
    payload.update(params)
    payload['networks'] = []  # This will be empty, too.
    assert_success(
        client.partial_update(ifc_pk_uri, **params),
        payload
    )


def test_filters(site, client):
    """Test field filters for Interfaces."""
    ifc_uri = site.list_uri('interface')
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    # Create vlan Attribute
    client.create(attr_uri, name='vlan', resource_name='Interface')

    # Create Devices
    dev1_resp = client.create(dev_uri, hostname='foo-bar1')
    dev2_resp = client.create(dev_uri, hostname='foo-bar2')

    dev1 = get_result(dev1_resp)
    dev2 = get_result(dev2_resp)

    # Create Interfaces
    # foo-bar1:eth0
    dev1_eth0_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth0', attributes={'vlan': '100'},
        mac_address=0
    )
    dev1_eth0 = get_result(dev1_eth0_resp)

    # foo-bar1:eth1
    dev1_eth1_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth1', speed=40000, type=161,
        mac_address=1
    )
    dev1_eth1 = get_result(dev1_eth1_resp)

    # foo-bar2:eth0
    dev2_eth0_resp = client.create(
        ifc_uri, device=dev2['id'], name='eth0', description='foo-bar2:eth0',
        mac_address=3
    )
    dev2_eth0 = get_result(dev2_eth0_resp)

    # foo-bar2:eth1
    dev2_eth1_resp = client.create(
        ifc_uri, device=dev2['id'], name='eth1', type=161,
        parent_id=dev2_eth0['id'], mac_address=4
    )
    dev2_eth1 = get_result(dev2_eth1_resp)

    # Populate the Interface objects and retreive them for testing.
    interfaces_resp = client.get(ifc_uri)
    interfaces = get_result(interfaces_resp)

    # Test filter by name
    wanted = [dev1_eth0, dev2_eth0]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, name='eth0'),
        expected
    )

    # Test filter by device
    wanted = [dev1_eth0, dev1_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, device=dev1['id']),
        expected
    )

    # Test filter by device__hostname (on device)
    wanted = [dev1_eth0, dev1_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, device__hostname=dev1['hostname']),
        expected
    )

    # Test filter by device_hostname (on interface)
    wanted = [dev1_eth0, dev1_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, device_hostname=dev1['hostname']),
        expected
    )

    # Test filter by speed
    wanted = [dev1_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, speed=40000),
        expected
    )

    # Test filter by type
    wanted = [dev1_eth1, dev2_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, type=161),
        expected
    )

    # Test filter by description
    wanted = [dev2_eth0]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, description='foo-bar2:eth0'),
        expected
    )

    # Test filter by parent_id
    wanted = [dev2_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, parent_id=dev2_eth0['id']),
        expected
    )

    # Test filter by attributes
    wanted = [dev1_eth0]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(ifc_uri, attributes=['vlan=100']),
        expected
    )

    # Test filter by mac_address using various representations
    wanted = [dev1_eth1]
    expected = filter_interfaces(interfaces, wanted)
    mac_tests = (
        1,  # Integer
        '1',  # Integer as a string
        '00:00:00:00:00:01',  # String
    )
    for mac in mac_tests:
        assert_success(client.retrieve(ifc_uri, mac_address=mac), expected)


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

    dev1 = get_result(dev1_resp)
    dev2 = get_result(dev2_resp)

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

    dev1_eth0 = get_result(dev1_eth0_resp)
    dev1_eth1 = get_result(dev1_eth1_resp)
    dev2_eth0 = get_result(dev2_eth0_resp)
    dev2_eth1 = get_result(dev2_eth1_resp)

    # Populate the Interface objects and retreive them for testing.
    interfaces_resp = client.get(ifc_uri)
    interfaces = get_result(interfaces_resp)

    # INTERSECTION: vlan=300
    wanted = [dev1_eth0, dev1_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(query_uri, query='vlan=300'),
        expected
    )

    # INTERSECTION: vlan=300 scope=region
    wanted = [dev1_eth0]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(query_uri, query='vlan=300 scope=region'),
        expected
    )

    # DIFFERENCE: -scope=region
    wanted = [dev1_eth1, dev2_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(query_uri, query='-scope=region'),
        expected
    )

    # UNION: scope=global +vlan=400
    wanted = [dev1_eth1, dev2_eth1]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(query_uri, query='scope=global +vlan=400'),
        expected
    )

    # UNIQUE: vlan=300 scope=region
    wanted = [dev1_eth0]
    expected = filter_interfaces(interfaces, wanted)
    assert_success(
        client.retrieve(query_uri, query='vlan=300 scope=region', unique=True),
        expected
    )

    # ERROR: not unique
    assert_error(
        client.retrieve(query_uri, query='scope=global +vlan=400', unique=True),
        status.HTTP_400_BAD_REQUEST
    )

    # ERROR: no result
    assert_error(
        client.retrieve(query_uri, query='scope=local vlan=400', unique=True),
        status.HTTP_400_BAD_REQUEST
    )

    # ERROR: bad query
    assert_error(
        client.retrieve(query_uri, query='bacon=delicious'),
        status.HTTP_400_BAD_REQUEST
    )


def test_deletion(site, client):
    """Test deletion of Interfaces."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')

    dev1_resp = client.create(dev_uri, hostname='foo-bar1')
    dev1 = get_result(dev1_resp)

    # Create Interfaces
    dev1_eth0_resp = client.create(ifc_uri, device=dev1['id'], name='eth0')
    dev1_eth0 = get_result(dev1_eth0_resp)
    dev1_eth0_uri = site.detail_uri('interface', id=dev1_eth0['id'])

    dev1_eth1_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth1', parent_id=dev1_eth0['id']
    )
    dev1_eth1 = get_result(dev1_eth1_resp)
    dev1_eth1_uri = site.detail_uri('interface', id=dev1_eth1['id'])

    # Don't allow delete when there's a child Interface
    assert_error(client.delete(dev1_eth0_uri), status.HTTP_409_CONFLICT)

    # Delete the child Interface
    client.delete(dev1_eth1_uri)

    # And safely delete the parent Network
    assert_deleted(client.delete(dev1_eth0_uri))

    # Delete based on natural key
    dev1_eth2_resp = client.create(ifc_uri, device=dev1['id'], name='eth2')
    dev1_eth2 = get_result(dev1_eth2_resp)
    natural_key = slugify_interface(**dev1_eth2)
    dev1_eth2_natural_uri = site.detail_uri('interface', id=natural_key)
    assert_deleted(client.delete(dev1_eth2_natural_uri))


def test_detail_routes(site, client):
    """Test detail routes for Interfaces objects."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')
    net_uri = site.list_uri('network')

    dev_resp = client.create(dev_uri, hostname='foo-bar1')
    dev = get_result(dev_resp)

    net_resp = client.create(net_uri, cidr='10.1.1.0/24')
    net = get_result(net_resp)

    # Create a simple interface with addresses

    set_addresses = ['10.1.1.1/32', '10.1.1.2/32', '10.1.1.3/32']

    ifc_resp = client.create(
        ifc_uri, device=dev['id'], name='eth0', addresses=set_addresses
    )
    ifc = get_result(ifc_resp)
    ifc_obj_uri = site.detail_uri('interface', id=ifc['id'])

    # Fetch the Network address objects
    addresses_resp = client.retrieve(
        net_uri, include_ips=True, include_networks=False
    )
    addresses = get_result(addresses_resp)
    expected = addresses

    # Verify Interface.addresses
    addresses_uri = reverse('interface-addresses', args=(site.id, ifc['id']))
    assert_success(client.retrieve(addresses_uri), expected)

    # Verify Interface.addresses by natural key
    natural_key = slugify_interface(**ifc)
    addresses_natural_uri = reverse(
        'interface-addresses', args=(site.id, natural_key))
    assert_success(client.retrieve(addresses_natural_uri), expected)

    # Verify Interface.networks
    networks_uri = reverse('interface-networks', args=(site.id, ifc['id']))
    expected = [net]
    assert_success(client.retrieve(networks_uri), expected)

    # Verify Interface.networks by natural key
    networks_natural_uri = reverse(
        'interface-networks', args=(site.id, natural_key))
    assert_success(client.retrieve(networks_natural_uri), expected)

    # Update the interface name to be more complex, and test again to verify
    # detail routes for more complex interface names
    params = {'name': 'xe-1/2/3:10.0'}
    ifc_resp = client.partial_update(ifc_obj_uri, **params)
    ifc = get_result(ifc_resp)
    # Build the new natural key
    natural_key = slugify_interface(**ifc)

    # Verify Interface.addresses by natural key with a complex interface name
    addresses_natural_uri = reverse(
        'interface-addresses', args=(site.id, natural_key))
    expected = addresses
    assert_success(client.retrieve(addresses_natural_uri), expected)

    # Verify Interface.networks by natural key with a complex interface name
    networks_natural_uri = reverse(
        'interface-networks', args=(site.id, natural_key))
    expected = [net]
    assert_success(client.retrieve(networks_natural_uri), expected)

    # Verify assignments
    # FIXME(jathan): Assignments detail route testing is NYI!
    # LOL nothing happens here
