import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, assert_deleted, Client
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
        user_client.create("/sites/1/devices",
            hostname="device1", attributes={"attr1": "foo"}
        ),
        403
    )

    # Missing required field (hostname)
    assert_error(
        admin_client.create("/sites/1/devices",
            attributes={"attr1": "foo"}
        ),
        400
    )

    # Verify Successful Creation
    assert_created(
        admin_client.create("/sites/1/devices",
            hostname="device1", attributes={"attr1": "foo"}
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


def test_update(tornado_server):
    admin_client = Client(tornado_server, "admin")
    user_client = Client(tornado_server, "user")

    admin_client.create("/sites", name="Test Site")  # 1
    admin_client.create(
        "/sites/1/attributes", resource_name="Device", name="attr1"
    )  # 1
    admin_client.create("/sites/1/devices",
        hostname="foo", attributes={"attr1": "foo"}
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

    client.create("/sites/1/devices", hostname="device1")  # 1
    client.create("/sites/1/devices", hostname="device2")  # 2

    assert_deleted(client.delete("/sites/1/devices/1"))
