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
    Client, load, filter_devices
)


log = logging.getLogger(__name__)


def test_creation(live_server, user, site):
    admin_client = Client(live_server, user='admin')
    user_client = Client(live_server, user='user')

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    admin_client.create(attr_uri, resource_name='Device', name='attr1')

    # Invalid permissions
    assert_error(
        user_client.create(
            dev_uri, hostname='device1', attributes={'attr1': 'foo'}
        ),
        status.HTTP_403_FORBIDDEN
    )

    # Missing required field (hostname)
    assert_error(
        admin_client.create(dev_uri, attributes={'attr1': 'foo'}),
        status.HTTP_400_BAD_REQUEST
    )

    # Null hostname
    assert_error(
        admin_client.create(dev_uri, hostname=None),
        status.HTTP_400_BAD_REQUEST
    )

    # Verify successful creation
    dev_resp = admin_client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )
    dev = dev_resp.json()['data']['device']
    dev_obj_uri = site.detail_uri('device', id=dev['id'])

    assert_created(dev_resp, dev_obj_uri)

    # Verify successful get of all Devices
    expected = dev_resp.json()['data']
    expected['devices'] = [expected.pop('device')]
    expected.update({'limit': None, 'offset': 0, 'total': 1})

    assert_success(admin_client.get(dev_uri), expected)

    # Verify successful get of single Device
    assert_success(admin_client.get(dev_obj_uri), {'device': dev})


def test_collection_creation(site, client):
    # URIs
    dev_uri = site.list_uri('device')

    # Successfully create a collection of Devices
    collection = [
        {'hostname': 'device1'},
        {'hostname': 'device2'},
        {'hostname': 'device3'},
    ]
    collection_response = client.post(
        dev_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Devices
    output = collection_response.json()
    output['data'].update({
        'limit': None, 'offset': 0, 'total': len(collection)
    })

    assert_success(client.get(dev_uri), output['data'])


def test_filters(site, client):
    """Test hostname/attribute filters for Devices."""

    # URIs
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the Device objects
    dev_resp = client.post(dev_uri, data=load('devices.json'))
    devices_out = dev_resp.json()['data']
    devices = devices_out['devices']

    # Test lookup by hostname
    expected = copy.deepcopy(devices_out)
    wanted = ['foo-bar3']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(dev_uri, hostname='foo-bar3'),
        expected
    )

    # Test lookup by attributes
    wanted = ['foo-bar2', 'foo-bar3']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(dev_uri, attributes='foo=baz'),
        expected
    )

    # Test lookup with multiple attributes
    wanted = ['foo-bar3']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(dev_uri, attributes=['foo=baz', 'cluster=lax']),
        expected
    )


def test_set_queries(client, site):
    """Test set queries for Devices."""

    # URIs
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')
    query_uri = site.query_uri('device')

    # Pre-load the attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the device objects.
    dev_resp = client.post(dev_uri, data=load('devices.json'))
    devices_out = dev_resp.json()['data']
    devices = devices_out['devices']

    # INTERSECTION: foo=bar
    expected = copy.deepcopy(devices_out)
    wanted = ['foo-bar1', 'foo-bar4']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='foo=bar'),
        expected
    )

    # INTERSECTION: foo=bar owner=jathan
    wanted = ['foo-bar1']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='foo=bar owner=jathan'),
        expected
    )

    # DIFFERENCE: -owner=gary
    wanted = ['foo-bar1', 'foo-bar3']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='-owner=gary'),
        expected
    )

    # UNION: cluster +foo=baz
    wanted = ['foo-bar1', 'foo-bar2', 'foo-bar3']
    expected['devices'] = filter_devices(devices, wanted)
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(query_uri, query='cluster +foo=baz'),
        expected
    )


def test_update(live_server, user, site):
    admin_client = Client(live_server, user='admin')
    user_client = Client(live_server, user='user')

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    admin_client.create(attr_uri, resource_name='Device', name='attr1')
    dev_resp = admin_client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )

    # Extract the device object from the response payload so we can play with
    # it during update tests.
    device = dev_resp.json()['data']['device']
    dev_obj_uri = site.detail_uri('device', id=device['id'])

    # Empty update should only clear attributes.
    params = {'hostname': 'foo'}
    device.update(params)
    device['attributes'] = {}

    assert_success(
        admin_client.update(dev_obj_uri, **params),
        {'device': device}
    )

    # Now put attributes back and change hostname
    params = {'hostname': 'bar', 'attributes': {'attr1': 'foo'}}
    device.update(params)

    assert_success(
        admin_client.update(dev_obj_uri, **params),
        {'device': device}
    )

    # Invalid permissions
    assert_error(user_client.update(dev_obj_uri), status.HTTP_403_FORBIDDEN)


def test_deletion(site, client):
    dev_uri = site.list_uri('device')
    attr_uri = site.list_uri('attribute')

    client.create(attr_uri, resource_name='Device', name='attr1')

    # Create one Device with an Attribute so that we can confirm is is safely
    # deleted.
    dev1_resp = client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )
    dev1 = dev1_resp.json()['data']['device']
    dev1_obj_uri = site.detail_uri('device', id=dev1['id'])

    # Device 2
    client.create(dev_uri, hostname='device2')

    # Delete Device 1 w/ Attribute
    assert_deleted(client.delete(dev1_obj_uri))


def test_detail_routes(site, client):
    """Test detail routes for Devices."""
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

    # Fetch the Interface objects
    interfaces_resp = client.get(ifc_uri)
    interfaces_out = interfaces_resp.json()['data']
    interfaces = interfaces_out['interfaces']

    # Verify Device.interfaces
    ifaces_uri = reverse('device-interfaces', args=(site.id, dev1['id']))
    expected = {
        'total': len(interfaces),
        'limit': None,
        'offset': 0,
        'interfaces': interfaces,
    }
    assert_success(client.retrieve(ifaces_uri), expected)
