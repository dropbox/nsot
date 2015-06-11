import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, assert_deleted, Client,
    load_json, run_set_queries
)


def test_creation(tornado_server):
    admin_client = Client(tornado_server, "admin")
    user_client = Client(tornado_server, "user")

    admin_client.create("/sites", name="Test Site")  # 1
    admin_client.create(
        "/sites/1/attributes",
        resource_name="Device", name="attr1"
    )  # 1

    # Invalid permissions
    assert_error(
        user_client.create(
            "/sites/1/devices", hostname="device1", attributes={"attr1": "foo"}
        ),
        403
    )

    # Missing required field (hostname)
    assert_error(
        admin_client.create(
            "/sites/1/devices", attributes={"attr1": "foo"}
        ),
        400
    )

    # Null hostname
    assert_error(
        admin_client.create(
            "/sites/1/devices",
            hostname=None
        ),
        400
    )

    # Verify Successful Creation
    assert_created(
        admin_client.create(
            "/sites/1/devices", hostname="device1", attributes={"attr1": "foo"}
        ),
        "/api/sites/1/devices/1"
    )

    # Verify Successful get of all Devices
    assert_success(
        admin_client.get("/sites/1/devices"),
        {
            "devices": [{
                "attributes": {"attr1": "foo"},
                "id": 1,
                "site_id": 1,
                "hostname": "device1",
            }],
            "limit": None,
            "offset": 0,
            "total": 1,
        }

    )

    # Verify Successful get of single Device
    assert_success(
        admin_client.get("/sites/1/devices/1"),
        {"device": {
            "attributes": {"attr1": "foo"},
            "id": 1,
            "site_id": 1,
            "hostname": "device1",
        }}
    )


def test_collection_creation(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")  # 1

    # Successfully create a collection of Devices
    collection = [
        {"hostname": "device1"},
        {"hostname": "device2"},
        {"hostname": "device3"},
    ]
    collection_response = client.create(
        "/sites/1/devices",
        devices=collection
    )
    assert_created(collection_response, None)

    # Successfully get all created Devices
    output = collection_response.json()
    output['data'].update({"limit": None, "offset": 0})

    assert_success(
        client.get("/sites/1/devices"),
        output['data'],
    )


def test_filters(tornado_server):
    """Test hostname/attribute filters for Devices."""
    client = Client(tornado_server)

    client.create('/sites', name='Test Site')  # 1

    # Pre-load the attributes
    attr_data = load_json('attributes.json')
    client.create(
        '/sites/1/attributes',
        attributes=attr_data['attributes']
    )

    # Populate the device objects.
    device_data = load_json('devices.json')
    client.create(
        '/sites/1/devices',
        devices=device_data['devices']
    )

    # Test lookup by hostnme
    hostname_output = load_json('devices/filter1.json')
    assert_success(
        client.get("/sites/1/devices?hostname=foo-bar3"),
        hostname_output['data'],
    )

    # Test lookup by attributes
    attr_output = load_json('devices/filter2.json')
    assert_success(
        client.get("/sites/1/devices?attributes=foo=baz"),
        attr_output['data'],
    )

    # Test lookup with multiple attributes
    multiattr_output = load_json('devices/filter3.json')
    assert_success(
        client.get("/sites/1/devices?attributes=foo=baz&attributes=cluster=lax"),
        multiattr_output['data'],
    )


def test_set_queries(tornado_server):
    """Test set queries for Devices."""
    client = Client(tornado_server)

    client.create('/sites', name='Test Site')  # 1

    # Pre-load the attributes
    attr_data = load_json('attributes.json')
    client.create(
        '/sites/1/attributes',
        attributes=attr_data['attributes']
    )

    # Populate the device objects.
    device_data = load_json('devices.json')
    client.create(
        '/sites/1/devices',
        devices=device_data['devices']
    )

    # Mapping of query string to file containing expected response data for
    # each query.
    device_queries = (
        # INTERSECTION: foo=bar
        ('foo=bar', 'query1.json'),
        # INTERSECTION: foo=bar owner=jathan
        ('foo=bar owner=jathan', 'query2.json'),
        # DIFFERENCE: -owner=gary
        ('-owner=gary', 'query3.json'),
        # UNION: cluster +foo=baz
        ('cluster +foo=baz', 'query4.json'),
    )
    run_set_queries('devices', client, device_queries)


def test_update(tornado_server):
    admin_client = Client(tornado_server, "admin")
    user_client = Client(tornado_server, "user")

    admin_client.create("/sites", name="Test Site")  # 1
    admin_client.create(
        "/sites/1/attributes", resource_name="Device", name="attr1"
    )  # 1
    admin_client.create(
        "/sites/1/devices", hostname="foo", attributes={"attr1": "foo"}
    )

    # Empty Update should only clear attributes.
    assert_success(
        admin_client.update("/sites/1/devices/1", hostname="foo"),
        {"device": {
            "attributes": {},
            "id": 1,
            "site_id": 1,
            "hostname": "foo",
        }}
    )

    # Now put attributes back and change hostname
    assert_success(
        admin_client.update(
            "/sites/1/devices/1", hostname="bar", attributes={"attr1": "foo"}
        ),
        {"device": {
            "attributes": {"attr1": "foo"},
            "id": 1,
            "site_id": 1,
            "hostname": "bar",
        }}
    )

    # Invalid permissions
    assert_error(
        user_client.update("/sites/1/devices/1"),
        403
    )


def test_deletion(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")
    client.create(
        "/sites/1/attributes", resource_name="Device", name="attr1"
    )  # 1

    # Create one Device with an attribute, so that we can confirm it is safely
    # deleted.
    client.create("/sites/1/devices", hostname="device1", attributes={'attr1': 'foo'})  # 1
    client.create("/sites/1/devices", hostname="device2")  # 2

    assert_deleted(client.delete("/sites/1/devices/1"))
