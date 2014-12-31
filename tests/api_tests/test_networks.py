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
    admin_client.create("/sites/1/network_attributes", name="attr1")  # 1

    # Invalid permissions
    assert_error(
        user_client.create("/sites/1/networks",
            cidr="10.0.0.0/24", attributes={"attr1": "foo"}
        ),
        403
    )

    # Missing required field (cidr)
    assert_error(
        admin_client.create("/sites/1/networks",
            attributes={"attr1": "foo"}
        ),
        400
    )

    # Verify Successful Creation
    assert_created(
        admin_client.create("/sites/1/networks",
            cidr="10.0.0.0/24", attributes={"attr1": "foo"}
        ),
        "/api/sites/1/networks/1"
    )

    # Verify Successful get of all Networks
    assert_success(
        admin_client.get("/sites/1/networks"),
        {"networks": [{
            "attributes": {"attr1": "foo"},
            "id": 1,
            "ip_version": "4",
            "is_ip": False,
            "network_address": "10.0.0.0",
            "prefix_length": 24,
            "site_id": 1
        }]}

    )

    # Verify Successful get of single Network
    assert_success(
        admin_client.get("/sites/1/networks/1"),
        {"network": {
            "attributes": {"attr1": "foo"},
            "id": 1,
            "ip_version": "4",
            "is_ip": False,
            "network_address": "10.0.0.0",
            "prefix_length": 24,
            "site_id": 1
        }}
    )


def test_update(tornado_server):
    admin_client = Client(tornado_server, "admin")
    user_client = Client(tornado_server, "user")

    admin_client.create("/sites", name="Test Site")  # 1
    admin_client.create("/sites/1/network_attributes", name="attr1")  # 1
    admin_client.create("/sites/1/networks",
        cidr="10.0.0.0/24", attributes={"attr1": "foo"}
    )

    # Empty Update should only clear attributes.
    assert_success(
        admin_client.update("/sites/1/networks/1"),
        {"network": {
            "attributes": {},
            "id": 1,
            "ip_version": "4",
            "is_ip": False,
            "network_address": "10.0.0.0",
            "prefix_length": 24,
            "site_id": 1
        }}
    )

    # Now put attributes back
    assert_success(
        admin_client.update("/sites/1/networks/1", attributes={"attr1": "foo"}),
        {"network": {
            "attributes": {"attr1": "foo"},
            "id": 1,
            "ip_version": "4",
            "is_ip": False,
            "network_address": "10.0.0.0",
            "prefix_length": 24,
            "site_id": 1
        }}
    )

    # Invalid permissions
    assert_error(
        user_client.update("/sites/1/networks/1"),
        403
    )

def test_deletion(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")

    client.create("/sites/1/networks", cidr="10.0.0.0/24")  # 1
    client.create("/sites/1/networks", cidr="10.0.0.1/32")  # 2

    # Don't allow delete when there's an attached subnet/ip
    assert_error(client.delete("/sites/1/networks/1"), 409)

    client.delete("/sites/1/networks/2")

    assert_deleted(client.delete("/sites/1/networks/1"))

