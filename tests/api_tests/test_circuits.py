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
    Client, load, filter_circuits, get_result
)


log = logging.getLogger(__name__)


def test_creation(site, client):
    """Test basic creation of a Circuit."""
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')
    net_uri = site.list_uri('network')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Parent network for interface assignments
    net_resp = client.create(net_uri, cidr='10.32.0.0/24')
    net = get_result(net_resp)

    # Interfaces
    if_a_resp = client.create(
        ifc_uri, device=dev_a['id'], name='eth0', addresses=['10.32.0.1/32']
    )
    if_a = get_result(if_a_resp)
    if_z_resp = client.create(
        ifc_uri, device=dev_z['id'], name='eth0', addresses=['10.32.0.2/32']
    )
    if_z = get_result(if_z_resp)

    # Missing required field (endpoint_a, endoint_z)
    assert_error(
        client.create(cir_uri, attributes={'attr1': 'foo'}),
        status.HTTP_400_BAD_REQUEST
    )

    # Null name is bad
    assert_error(
        client.create(
            cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id'], name=None
        ),
        status.HTTP_400_BAD_REQUEST
    )

    # Verify successful creation
    cir_resp = client.create(
        cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id']
    )
    cir = get_result(cir_resp)
    cir_obj_uri = site.detail_uri('circuit', id=cir['id'])

    assert_created(cir_resp, cir_obj_uri)

    # Try to create another circuit with the same interfaces
    assert_error(
        client.create(
            cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id']
        ),
        status.HTTP_400_BAD_REQUEST
    )

    # Try to create another circuit with interfaces A/Z inverted.
    assert_error(
        client.create(
            cir_uri, endpoint_a=if_z['id'], endpoint_z=if_a['id']
        ),
        status.HTTP_400_BAD_REQUEST
    )

    # Create a circuit referencing interfaces with natural keys
    ae1_a = get_result(client.create(ifc_uri, device=dev_a['id'], name='ae1'))
    ae1_z = get_result(client.create(ifc_uri, device=dev_z['id'], name='ae1'))

    cir2_resp = client.create(
        cir_uri, endpoint_a=ae1_a['name_slug'], endpoint_z=ae1_z['name_slug']
    )
    cir2 = get_result(cir2_resp)
    cir2_obj_uri = site.detail_uri('circuit', id=cir2['id'])

    assert_created(cir2_resp, cir2_obj_uri)

    # Verify successful get of single Circuit
    assert_success(client.get(cir_obj_uri), cir)

    # Verify successful get of single Circuit by natural key
    natural_key = cir['name']
    cir_natural_uri = site.detail_uri('circuit', id=natural_key)
    assert_success(client.get(cir_natural_uri), cir)

    # Verify successful retrieval of all Circuits
    circuits = [cir, cir2]
    expected = circuits
    assert_success(client.get(cir_uri), expected)


def test_bulk_operations(site, client):
    """Test creating/updating multiple Circuits at once."""
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Interfaces (2-pairs of A/Z)
    # 1st pair
    if_a1_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a1 = get_result(if_a1_resp)
    if_z1_resp = client.create(ifc_uri, device=dev_z['id'], name='eth0')
    if_z1 = get_result(if_z1_resp)
    # 2nd pair
    if_a2_resp = client.create(ifc_uri, device=dev_a['id'], name='eth1')
    if_a2 = get_result(if_a2_resp)
    if_z2_resp = client.create(ifc_uri, device=dev_z['id'], name='eth1')
    if_z2 = get_result(if_z2_resp)

    # Successfully create a collection of Circuits
    collection = [
        {'endpoint_a': if_a1['id'], 'endpoint_z': if_z1['id']},
        {'endpoint_a': if_a2['id'], 'endpoint_z': if_z2['id']},
    ]
    collection_response = client.post(
        cir_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Circuits
    output = collection_response.json()
    expected = get_result(output)

    assert_success(client.get(cir_uri), expected)

    # Test update of all created Circuit (name: foo => wtf)
    updated = copy.deepcopy(expected)
    for item in updated:
        item['name'] = item['name'].replace('foo', 'wtf')
        item['name_slug'] = item['name_slug'].replace('foo', 'wtf')
    updated_resp = client.put(cir_uri, data=json.dumps(updated))
    expected = updated_resp.json()

    assert updated == expected


def test_update(site, client):
    """Test update of an existing interface w/ an address."""
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Interfaces
    if_a_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a = get_result(if_a_resp)
    if_z_resp = client.create(ifc_uri, device=dev_z['id'], name='eth0')
    if_z = get_result(if_z_resp)

    # Create basic circuit
    cir_resp = client.create(
        cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id']
    )
    cir = get_result(cir_resp)
    cir_obj_uri = site.detail_uri('circuit', id=cir['id'])

    # Update circuit to use a different Z-side (using natural key).
    if_z2_resp = client.create(ifc_uri, device=dev_z['id'], name='eth1')
    if_z2 = get_result(if_z2_resp)

    payload = copy.deepcopy(cir)
    params = copy.deepcopy(payload)
    params['endpoint_z'] = if_z2['name_slug']
    payload.update(params)

    assert_success(
        client.update(cir_obj_uri, **params),
        payload
    )

    # Update circuit Z-side using ID (should still match previous payload)
    params['endpoint_z'] = if_z2['id']
    assert_success(
        client.update(cir_obj_uri, **params),
        payload
    )

    # Updating circuit to have no A-size should fail!
    params['endpoint_a'] = None
    assert_error(
        client.update(cir_obj_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )
    params['endpoint_a'] = if_a['name_slug']  # Restore if_a.name_slug

    # Update circuit to have no Z-side.
    params['endpoint_z'] = None
    params['name'] = 'foo-bar1:eth0_None'
    payload.update(params)

    # Read-only computed parameters
    payload['name_slug'] = 'foo-bar1:eth0_None'

    assert_success(
        client.update(cir_obj_uri, **params),
        payload
    )

    # Check the circuit's name is foo-bar1:eth0_None
    expected_name = '%s:%s_%s' % (if_a['device_hostname'], if_a['name'], None)
    obj_resp = client.get(cir_obj_uri)
    obj = get_result(obj_resp)
    assert obj['name'] == expected_name

    # Restore circuit back to normal using natural_key
    params['endpoint_z'] = if_z['name_slug']
    params['name'] = 'foo-bar1:eth0_foo-bar2:eth0'
    payload.update(params)

    natural_key = obj['name']
    cir_natural_uri = site.detail_uri('circuit', id=natural_key)

    assert_success(
        client.update(cir_natural_uri, **params),
        payload
    )

    # Create another A-side interface on dev_a
    if_a2_resp = client.create(ifc_uri, device=dev_a['id'], name='eth1')
    if_a2 = get_result(if_a2_resp)

    # Create another circuit
    cir2_resp = client.create(
        cir_uri, endpoint_a=if_a2['id'], endpoint_z=if_z2['id']
    )
    cir2 = get_result(cir2_resp)
    cir2_obj_uri = site.detail_uri('circuit', id=cir2['id'])

    # Circuit name must be unique (try setting cir2 to cir's name)
    params = copy.deepcopy(cir2)
    params['name'] = cir['name']
    assert_error(
        client.update(cir2_obj_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )


def test_partial_update(site, client):
    """Test PATCH operations to partially update a Circuit."""
    attr_uri = site.list_uri('attribute')
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Interfaces
    if_a_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a = get_result(if_a_resp)
    if_z_resp = client.create(ifc_uri, device=dev_z['id'], name='eth0')
    if_z = get_result(if_z_resp)

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Create basic circuit
    cir_resp = client.create(
        cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id'],
        attributes={'cid': 'abc123', 'vendor': 'acme'}
    )
    cir = get_result(cir_resp)
    cir_obj_uri = site.detail_uri('circuit', id=cir['id'])

    # Assert that a partial update on PUT will fail
    params = {'name': 'mycircuit'}
    assert_error(
        client.update(cir_obj_uri, **params),
        status.HTTP_400_BAD_REQUEST
    )

    # Update only name
    payload = copy.deepcopy(cir)
    payload.update(params)
    payload['name_slug'] = 'mycircuit'

    assert_success(
        client.partial_update(cir_obj_uri, **params),
        payload
    )

    # Update only attributes
    params = {'attributes': {}}  # Nuke 'em
    payload.update(params)
    assert_success(
        client.partial_update(cir_obj_uri, **params),
        payload
    )

    # Update only endpoint_z (to null)
    params = {'endpoint_z': None}
    payload.update(params)
    assert_success(
        client.partial_update(cir_obj_uri, **params),
        payload
    )


def test_filters(site, client):
    """Test field filters for Interfaces."""
    attr_uri = site.list_uri('attribute')
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Interfaces (2-pairs of A/Z)
    # 1st pair
    if_a1_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a1 = get_result(if_a1_resp)
    if_z1_resp = client.create(ifc_uri, device=dev_z['id'], name='eth0')
    if_z1 = get_result(if_z1_resp)
    # 2nd pair
    if_a2_resp = client.create(ifc_uri, device=dev_a['id'], name='eth1')
    if_a2 = get_result(if_a2_resp)
    if_z2_resp = client.create(ifc_uri, device=dev_z['id'], name='eth1')
    if_z2 = get_result(if_z2_resp)

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Create the circuits
    client.create(
        cir_uri, endpoint_a=if_a1['id'], endpoint_z=if_z1['id'],
        attributes={'cid': 'abc123', 'vendor': 'acme'}
    )
    client.create(
        cir_uri, endpoint_a=if_a2['id'], endpoint_z=if_z2['id'],
        attributes={'cid': 'abc246', 'vendor': 'acme'}
    )

    # Populate the Circuit objects and retreive them for testing.
    circuits_resp = client.get(cir_uri)
    circuits = get_result(circuits_resp)
    cir1, cir2 = circuits

    # Test filter by name
    wanted = [cir1]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(cir_uri, name='foo-bar1:eth0_foo-bar2:eth0'),
        expected
    )

    # Test filter by endpoint_a
    wanted = [cir2]
    expected = filter_circuits(circuits, wanted)
    # by ID
    assert_success(
        client.retrieve(cir_uri, endpoint_a=if_a2['id']),
        expected
    )
    # by natural key
    assert_success(
        client.retrieve(cir_uri, endpoint_a=if_a2['name_slug']),
        expected
    )

    # Test filter by endpoint_z
    wanted = [cir1]
    expected = filter_circuits(circuits, wanted)
    # by ID
    assert_success(
        client.retrieve(cir_uri, endpoint_z=if_z1['id']),
        expected
    )
    # by natural key
    assert_success(
        client.retrieve(cir_uri, endpoint_z=if_z1['name_slug']),
        expected
    )

    # Test filter by attributes (cidr=abc246)
    wanted = [cir2]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(cir_uri, attributes=['cid=abc246']),
        expected
    )

    # Test filter by attributes (vendor=acme)
    wanted = [cir1, cir2]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(cir_uri, attributes=['vendor=acme']),
        expected
    )


def test_set_queries(client, site):
    """Test set queries for Interfaces."""
    # URIs
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    attr_uri = site.list_uri('attribute')
    ifc_uri = site.list_uri('interface')
    query_uri = site.query_uri('circuit')

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Interfaces (4-pairs of A/Z)
    # 1st pair
    if_a1_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a1 = get_result(if_a1_resp)
    if_z1_resp = client.create(ifc_uri, device=dev_z['id'], name='eth0')
    if_z1 = get_result(if_z1_resp)
    # 2nd pair
    if_a2_resp = client.create(ifc_uri, device=dev_a['id'], name='eth1')
    if_a2 = get_result(if_a2_resp)
    if_z2_resp = client.create(ifc_uri, device=dev_z['id'], name='eth1')
    if_z2 = get_result(if_z2_resp)
    # 3rd pair
    if_a3_resp = client.create(ifc_uri, device=dev_a['id'], name='eth2')
    if_a3 = get_result(if_a3_resp)
    if_z3_resp = client.create(ifc_uri, device=dev_z['id'], name='eth2')
    if_z3 = get_result(if_z3_resp)
    # 3rd pair
    if_a4_resp = client.create(ifc_uri, device=dev_a['id'], name='eth3')
    if_a4 = get_result(if_a4_resp)
    if_z4_resp = client.create(ifc_uri, device=dev_z['id'], name='eth3')
    if_z4 = get_result(if_z4_resp)

    # Create 4x circuits
    client.create(
        cir_uri, endpoint_a=if_a1['id'], endpoint_z=if_z1['id'],
        attributes={'cid': 'abc123', 'vendor': 'acme'}
    )
    client.create(
        cir_uri, endpoint_a=if_a2['id'], endpoint_z=if_z2['id'],
        attributes={'cid': 'abc246', 'vendor': 'acme'}
    )
    client.create(
        cir_uri, endpoint_a=if_a3['id'], endpoint_z=if_z3['id'],
        attributes={'cid': 'xyz123', 'vendor': 'blamco'}
    )
    client.create(
        cir_uri, endpoint_a=if_a4['id'], endpoint_z=if_z4['id'],
        attributes={'cid': 'xyz246', 'vendor': 'jathcorp'}
    )

    # Populate the Interface objects and retreive them for testing.
    circuits_resp = client.get(cir_uri)
    circuits = get_result(circuits_resp)
    cir1, cir2, cir3, cir4 = circuits

    # INTERSECTION: vendor=acme
    wanted = [cir1, cir2]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(query_uri, query='vendor=acme'),
        expected
    )
    # INTERSECTION: cid=abc246 vendor=acme
    wanted = [cir2]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(query_uri, query='cid=abc246 vendor=acme'),
        expected
    )

    # DIFFERENCE: -vendor=acme
    wanted = [cir3, cir4]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(query_uri, query='-vendor=acme'),
        expected
    )

    # UNION: vendor=blamco +vendor=jathcorp
    wanted = [cir3, cir4]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(query_uri, query='vendor=blamco +vendor=jathcorp'),
        expected
    )

    # UNIQUE: cidr=abc123 vendor=acme
    wanted = [cir1]
    expected = filter_circuits(circuits, wanted)
    assert_success(
        client.retrieve(query_uri, query='cid=abc123 vendor=acme', unique=True),
        expected
    )

    # ERROR: not unique (vendor=acme)
    assert_error(
        client.retrieve(query_uri, query='vendor=acme', unique=True),
        status.HTTP_400_BAD_REQUEST
    )

    # ERROR: no result (vendor=bogus)
    assert_error(
        client.retrieve(query_uri, query='vendor=bogus', unique=True),
        status.HTTP_400_BAD_REQUEST
    )

    # ERROR: bad query
    assert_error(
        client.retrieve(query_uri, query='bacon=delicious'),
        status.HTTP_400_BAD_REQUEST
    )


def test_deletion(site, client):
    """Test deletion of Circuits."""
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')
    net_uri = site.list_uri('network')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Interfaces
    if_a_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a = get_result(if_a_resp)
    if_z_resp = client.create(ifc_uri, device=dev_z['id'], name='eth0')
    if_z = get_result(if_z_resp)

    # Circuit
    cir_resp = client.create(
        cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id']
    )
    cir = get_result(cir_resp)
    cir_obj_uri = site.detail_uri('circuit', id=cir['id'])

    # Don't allow Interface delete when member of a Circuit
    if_a_uri = site.detail_uri('interface', id=if_a['id'])
    assert_error(client.delete(if_a_uri), status.HTTP_409_CONFLICT)

    # Delete the Circuit
    assert_deleted(client.delete(cir_obj_uri))

    # And safely delete the A-side interface
    assert_deleted(client.delete(if_a_uri))

    # Delete by natural key (re-create interface and circuit first)
    if_a2_resp = client.create(ifc_uri, device=dev_a['id'], name='eth0')
    if_a2 = get_result(if_a2_resp)
    cir2_resp = client.create(
        cir_uri, endpoint_a=if_a2['id'], endpoint_z=if_z['id']
    )
    cir2 = get_result(cir2_resp)
    cir2_natural_uri = site.detail_uri('circuit', id=cir2['name'])
    assert_deleted(client.delete(cir2_natural_uri))


def test_detail_routes(site, client):
    """Test detail routes for Circuit objects."""
    cir_uri = site.list_uri('circuit')
    dev_uri = site.list_uri('device')
    ifc_uri = site.list_uri('interface')
    net_uri = site.list_uri('network')

    # Devices
    dev_a_resp = client.create(dev_uri, hostname='foo-bar1')
    dev_a = get_result(dev_a_resp)
    dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
    dev_z = get_result(dev_z_resp)

    # Parent network for interface assignments
    net_resp = client.create(net_uri, cidr='10.32.0.0/24')
    net = get_result(net_resp)

    # Interfaces
    if_a_resp = client.create(
        ifc_uri, device=dev_a['id'], name='eth0', addresses=['10.32.0.1/32']
    )
    if_a = get_result(if_a_resp)
    if_z_resp = client.create(
        ifc_uri, device=dev_z['id'], name='eth0', addresses=['10.32.0.2/32']
    )
    if_z = get_result(if_z_resp)

    # Circuit
    cir_resp = client.create(
        cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id']
    )
    cir = get_result(cir_resp)
    cir_obj_uri = site.detail_uri('circuit', id=cir['id'])

    # Verify Circuit.addresses
    addresses_resp = client.retrieve(net_uri, prefix_length=32)
    expected = get_result(addresses_resp)
    # pk
    addresses_uri = reverse('circuit-addresses', args=(site.id, cir['id']))
    assert_success(client.retrieve(addresses_uri), expected)
    # natural_key
    addresses_uri = reverse('circuit-addresses', args=(site.id, cir['name']))
    assert_success(client.retrieve(addresses_uri), expected)

    # Verify Circuit.interfaces
    interfaces_resp = client.retrieve(ifc_uri)
    expected = get_result(interfaces_resp)
    # pk
    interfaces_uri = reverse('circuit-interfaces', args=(site.id, cir['id']))
    assert_success(client.retrieve(interfaces_uri), expected)
    # natural_key
    interfaces_uri = reverse('circuit-interfaces', args=(site.id, cir['name']))
    assert_success(client.retrieve(interfaces_uri), expected)

    # Verify Circuit.devices
    devices_resp = client.retrieve(dev_uri)
    expected = get_result(devices_resp)
    # pk
    devices_uri = reverse('circuit-devices', args=(site.id, cir['id']))
    assert_success(client.retrieve(devices_uri), expected)
    # natural_key
    devices_uri = reverse('circuit-devices', args=(site.id, cir['name']))
    assert_success(client.retrieve(devices_uri), expected)

    # Verify Device.circuits
    dev_circuits_uri = reverse('device-circuits', args=(site.id, dev_a['id']))
    expected = [cir]
    assert_success(client.retrieve(dev_circuits_uri), expected)

    # Verify Interface.circuit
    ifc_circuit_uri = reverse('interface-circuit', args=(site.id, if_a['id']))
    expected = cir
    assert_success(client.retrieve(ifc_circuit_uri), expected)
