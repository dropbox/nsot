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
    Client, load, filter_devices, get_result
)


log = logging.getLogger(__name__)


def test_creation(client, user_client, user, site):
    """Test creation of Devices."""
    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    client.create(attr_uri, resource_name='Device', name='attr1')

    # Test invalid device name
    assert_error(
        client.create(
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
        client.create(dev_uri, attributes={'attr1': 'foo'}),
        status.HTTP_400_BAD_REQUEST
    )

    # Null hostname
    assert_error(
        client.create(dev_uri, hostname=None),
        status.HTTP_400_BAD_REQUEST
    )

    # Verify successful creation
    dev_resp = client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )
    dev = get_result(dev_resp)
    dev_obj_uri = site.detail_uri('device', id=dev['id'])

    assert_created(dev_resp, dev_obj_uri)

    # Verify successful get of all Devices
    payload = get_result(dev_resp)
    expected = [payload]

    assert_success(client.get(dev_uri), expected)

    # Verify successful get of single Device
    assert_success(client.get(dev_obj_uri), dev)

    # Verify successful get of single Device by natural_key
    dev_natural_uri = site.detail_uri('device', id=dev['hostname'])
    assert_success(client.get(dev_natural_uri), dev)


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
    payload = get_result(output)

    assert_success(client.get(dev_uri), payload)

    # Test bulk update to add attributes to each Device
    client.create(attr_uri, resource_name='Device', name='owner')
    updated = copy.deepcopy(payload)

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
    devices = get_result(dev_resp)

    # Test lookup by hostname
    wanted = ['foo-bar3']
    expected = filter_devices(devices, wanted)
    assert_success(
        client.retrieve(dev_uri, hostname='foo-bar3'),
        expected
    )

    # Test lookup by attributes
    wanted = ['foo-bar2', 'foo-bar3']
    expected = filter_devices(devices, wanted)
    assert_success(
        client.retrieve(dev_uri, attributes='foo=baz'),
        expected
    )

    # Test lookup with multiple attributes
    wanted = ['foo-bar3']
    expected = filter_devices(devices, wanted)
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
    devices = get_result(dev_resp)

    # INTERSECTION: foo=bar
    # expected = copy.deepcopy(devices_out)
    wanted = ['foo-bar1', 'foo-bar4']
    expected = filter_devices(devices, wanted)
    assert_success(
        client.retrieve(query_uri, query='foo=bar'),
        expected
    )

    # INTERSECTION: foo=bar owner=jathan
    wanted = ['foo-bar1']
    expected = filter_devices(devices, wanted)
    assert_success(
        client.retrieve(query_uri, query='foo=bar owner=jathan'),
        expected
    )

    # DIFFERENCE: -owner=gary
    wanted = ['foo-bar1', 'foo-bar3']
    expected = filter_devices(devices, wanted)
    assert_success(
        client.retrieve(query_uri, query='-owner=gary'),
        expected
    )

    # UNION: cluster +foo=baz
    wanted = ['foo-bar1', 'foo-bar2', 'foo-bar3']
    expected = filter_devices(devices, wanted)
    assert_success(
        client.retrieve(query_uri, query='cluster +foo=baz'),
        expected
    )

    # ERROR: bad query
    assert_error(
        client.retrieve(query_uri, query='chop=suey'),
        status.HTTP_400_BAD_REQUEST
    )


def test_update(client, user_client, user, site):
    """Test updating a device using pk."""
    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    client.create(attr_uri, resource_name='Device', name='attr1')
    dev_resp = client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )

    # Extract the device object from the response payload so we can play with
    # it during update tests.
    device = get_result(dev_resp)
    dev_obj_uri = site.detail_uri('device', id=device['id'])

    # Invalid permissions
    assert_error(user_client.update(dev_obj_uri), status.HTTP_403_FORBIDDEN)

    # If attributes aren't provided, it's an error.
    params = {'hostname': 'foo'}
    assert_error(
        client.update(dev_obj_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )

    # Update hostname and clear attributes.
    params = {'hostname': 'foo', 'attributes': {}}
    device.update(params)

    assert_success(
        client.update(dev_obj_uri, **params),
        device
    )

    # Now put attributes back and change hostname
    params = {'hostname': 'bar', 'attributes': {'attr1': 'foo'}}
    device.update(params)

    assert_success(
        client.update(dev_obj_uri, **params),
        device
    )


def test_update_natural_key(client, user_client, user, site):
    """Test updating a Device using natural_key."""
    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')

    client.create(attr_uri, resource_name='Device', name='attr1')
    dev_resp = client.create(
        dev_uri, hostname='device1', attributes={'attr1': 'foo'}
    )

    # Extract the device object from the response payload so we can play with
    # it during update tests.
    device = get_result(dev_resp)
    dev_pk_uri = site.detail_uri('device', id=device['id'])
    dev_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Update hostname and clear attributes.
    params = {'hostname': 'foo', 'attributes': {}}
    device.update(params)

    assert_success(
        client.update(dev_natural_uri, **params),
        device
    )

    # URI will have changed w/ the hostname
    new_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Now put attributes back and change hostname
    params = {'hostname': 'bar', 'attributes': {'attr1': 'foo'}}
    device.update(params)

    assert_success(
        client.update(new_natural_uri, **params),
        device
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
    device = get_result(dev_resp)
    dev_pk_uri = site.detail_uri('device', id=device['id'])
    dev_natural_uri = site.detail_uri('device', id=device['hostname'])

    # Now PATCH it by providing *only* the attributes, which wouldn't be
    # possible in a PUT
    params = {'attributes': {}}
    device.update(params)

    assert_success(
        client.partial_update(dev_pk_uri, **params),
        device
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
    dev1 = get_result(dev1_resp)
    dev1_obj_uri = site.detail_uri('device', id=dev1['id'])

    # Device 2
    client.create(dev_uri, hostname='device2')

    # Delete Device 1 w/ Attribute
    assert_deleted(client.delete(dev1_obj_uri))

    # Delete Device 3 by natural_key
    dev3_resp = client.create(dev_uri, hostname='device3')
    dev3 = get_result(dev3_resp)
    dev3_natural_uri = site.detail_uri('device', id=dev3['hostname'])
    assert_deleted(client.delete(dev3_natural_uri))


def test_detail_routes(site, client):
    """Test detail routes for Devices."""
    ifc_uri = site.list_uri('interface')
    dev_uri = site.list_uri('device')

    dev1_resp = client.create(dev_uri, hostname='foo-bar1')
    dev1 = get_result(dev1_resp)

    # Create Interfaces
    dev1_eth0_resp = client.create(ifc_uri, device=dev1['id'], name='eth0')
    dev1_eth0 = get_result(dev1_eth0_resp)
    dev1_eth0_uri = site.detail_uri('interface', id=dev1_eth0['id'])

    dev1_eth1_resp = client.create(
        ifc_uri, device=dev1['id'], name='eth1', parent=dev1_eth0['id']
    )
    dev1_eth1 = get_result(dev1_eth1_resp)
    dev1_eth1_uri = site.detail_uri('interface', id=dev1_eth1['id'])

    # Fetch the Interface objects
    interfaces_resp = client.get(ifc_uri)
    interfaces = get_result(interfaces_resp)

    # Verify Device.interfaces
    ifaces_uri = reverse('device-interfaces', args=(site.id, dev1['id']))
    expected = interfaces
    assert_success(client.retrieve(ifaces_uri), expected)

    # Now retrieve Device.interfaces by natural_key (hostname)
    natural_ifaces_uri = reverse('device-interfaces', args=(site.id, dev1['hostname']))
    assert_success(client.retrieve(natural_ifaces_uri), expected)
