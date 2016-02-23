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
    """Test creation of Devices."""
    admin_client = Client(live_server, user='admin')
    user_client = Client(live_server, user='user')

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    admin_client.create(attr_uri, resource_name='Device', name='attr1')

    # Test invalid device name
    assert_error(
        admin_client.create(
            dev_uri,
            hostname='invalid hostname'
        ),
        status.HTTP_400_BAD_REQUEST
    )

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

    # Verify successful get of single Device by natural_key
    dev_natural_uri = site.detail_uri('device', id=dev['hostname'])
    assert_success(admin_client.get(dev_natural_uri), {'device': dev})


def test_bulk_operations(site, client):
    """Test creating/updating multiple Devices at once."""
    # URIs
    attr_uri = site.list_uri('attribute')
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

    # Test bulk update to add attributes to each Device
    client.create(attr_uri, resource_name='Device', name='owner')
    updated = output['data']['devices']
    for item in updated:
        item['attributes'] = {'owner': 'jathan'}
    updated_resp = client.put(dev_uri, data=json.dumps(updated))
    expected = updated_resp.json()

    assert updated == expected


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
    """Test updating a device using pk."""
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

    # Invalid permissions
    assert_error(user_client.update(dev_obj_uri), status.HTTP_403_FORBIDDEN)

    # If attributes aren't provided, it's an error.
    params = {'hostname': 'foo'}
    assert_error(
        admin_client.update(dev_obj_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )

    # Update hostname and clear attributes.
    params = {'hostname': 'foo', 'attributes': {}}
    device.update(params)

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


def test_update_natural_key(live_server, user, site):
    """Test updating a Device using natural_key."""
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
    dev_pk_uri = site.detail_uri('device', id=device['id'])
    dev_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Update hostname and clear attributes.
    params = {'hostname': 'foo', 'attributes': {}}
    device.update(params)

    assert_success(
        admin_client.update(dev_natural_uri, **params),
        {'device': device}
    )

    # URI will have changed w/ the hostname
    new_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Now put attributes back and change hostname
    params = {'hostname': 'bar', 'attributes': {'attr1': 'foo'}}
    device.update(params)

    assert_success(
        admin_client.update(new_natural_uri, **params),
        {'device': device}
    )

    # URI will have changed w/ the hostname again
    final_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Invalid permissions
    assert_error(
        user_client.update(final_natural_uri), status.HTTP_403_FORBIDDEN
    )


def test_partial_update(site, client):
    """Test PATCH operations to partially update a Device."""
    dev_uri = site.list_uri('device')
    attr_uri = site.list_uri('attribute')

    client.create(attr_uri, resource_name='Device', name='attr1')
    dev_resp = client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )

    # Extract the device object from the response payload so we can play with
    # it during partial update tests.
    device = dev_resp.json()['data']['device']
    dev_pk_uri = site.detail_uri('device', id=device['id'])
    dev_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Now PATCH it by providing *only* the attributes, which wouldn't be
    # possible in a PUT
    params = {'attributes': {}}
    device.update(params)

    assert_success(
        client.partial_update(dev_pk_uri, **params),
        {'device': device}
    )

    # And just to make sure a PUT with the same payload fails...
    assert_error(
        client.update(dev_pk_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )


def test_deletion(site, client):
    """Test deletion of Devices."""
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

    # Delete Device 3 by natural_key
    dev3_resp = client.create(dev_uri, hostname='device3')
    dev3 = dev3_resp.json()['data']['device']
    dev3_natural_uri = site.detail_uri('device', id=dev3['hostname'])
    assert_deleted(client.delete(dev3_natural_uri))


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

    # Now retrieve Device.interfaces by natural_key (hostname)
    natural_ifaces_uri = reverse('device-interfaces', args=(site.id, dev1['hostname']))
    assert_success(client.retrieve(natural_ifaces_uri), expected)
