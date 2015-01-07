import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, assert_deleted, Client
)


def test_creation(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")  # 1

    # Test invalid attribute name
    assert_error(
        client.create("/sites/1/network_attributes", name="invalid attr1"),
        400
    )

    # Successfully create an attribute
    assert_created(
        client.create("/sites/1/network_attributes", name="attr1"),
        "/api/sites/1/network_attributes/1"
    )

    # Successfully get all Network Attributes
    assert_success(
        client.get("/sites/1/network_attributes"),
        {
            "network_attributes": [
                {
                    "id": 1, "name": "attr1", "description": "",
                    "required": False, "site_id": 1
                },
            ],
            "limit": None,
            "offset": 0,
            "total": 1,
        }

    )

    # Successfully get a single Network Attribute
    assert_success(
        client.get("/sites/1/network_attributes/1"),
        {"network_attribute": {
            "id": 1, "name": "attr1", "description": "",
            "required": False, "site_id": 1,
        }}

    )


def test_update(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")  # 1
    client.create("/sites/1/network_attributes", name="attr1")  # 1

    assert_success(
        client.update("/sites/1/network_attributes/1", description="Attribute 1"),
        {"network_attribute": {
            "id": 1, "name": "attr1", "description": "Attribute 1",
            "required": False, "site_id": 1
        }}
    )

    assert_success(
        client.update("/sites/1/network_attributes/1", required=True),
        {"network_attribute": {
            "id": 1, "name": "attr1", "description": "",
            "required": True, "site_id": 1
        }}
    )

    assert_success(
        client.update("/sites/1/network_attributes/1"),
        {"network_attribute": {
            "id": 1, "name": "attr1", "description": "",
            "required": False, "site_id": 1
        }}
    )


def test_deletion(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")
    client.create("/sites/1/network_attributes", name="attr1")
    client.create("/sites/1/networks",
        cidr="10.0.0.0/24", attributes={"attr1": "foo"}
    )

    # Don't allow delete when there's an attached network
    assert_error(client.delete("/sites/1/network_attributes/1"), 409)

    client.delete("/sites/1/networks/1")

    assert_deleted(client.delete("/sites/1/network_attributes/1"))

