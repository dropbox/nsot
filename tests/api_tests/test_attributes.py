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
        client.create(
            "/sites/1/attributes",
            resource_name="Network", name="invalid attr1"
        ),
        400
    )

    # Successfully create an attribute
    assert_created(
        client.create(
            "/sites/1/attributes",
            resource_name="Network", name="attr1"
        ),
        "/api/sites/1/attributes/1"
    )

    # Successfully get all Network Attributes
    assert_success(
        client.get("/sites/1/attributes"),
        {
            "attributes": [
                {
                    "id": 1, "name": "attr1", "description": "",
                    "required": False, "resource_name": "Network",
                    "site_id": 1, "display": False, "multi": False,
                    "constraints": {
                        "allow_empty": False,
                        "pattern": "",
                        "valid_values": []
                    }
                },
            ],
            "limit": None,
            "offset": 0,
            "total": 1,
        }

    )

    # Successfully get a single Network Attribute
    assert_success(
        client.get("/sites/1/attributes/1"),
        {"attribute": {
            "id": 1, "name": "attr1", "description": "", "resource_name": "Network",
            "required": False, "site_id": 1, "display": False, "multi": False,
            "constraints": {
                "allow_empty": False,
                "pattern": "",
                "valid_values": []
            }
        }}

    )


def test_collection_creation(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")  # 1

    # Successfully create a collection of Attributes
    collection = [
        {"name": "attr1", "resource_name": "Network"},
        {"name": "attr2", "resource_name": "Network"},
        {"name": "attr3", "resource_name": "Network"},
    ]
    collection_response = client.create(
        "/sites/1/attributes",
        attributes=collection
    )
    assert_created(collection_response, None)

    # Successfully get all created Attributes
    output = collection_response.json()
    output['data'].update({"limit": None, "offset": 0})

    assert_success(
        client.get("/sites/1/attributes"),
        output['data'],
    )


def test_update(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")  # 1
    client.create(
        "/sites/1/attributes",
        resource_name="Network", name="attr1"
    )  # 1

    assert_success(
        client.update("/sites/1/attributes/1", description="Attribute 1"),
        {"attribute": {
            "id": 1, "name": "attr1", "description": "Attribute 1",
            "required": False, "site_id": 1, "resource_name": "Network",
            "display": False, "multi": False,
            "constraints": {
                "allow_empty": False,
                "pattern": "",
                "valid_values": []
            }
        }}
    )

    assert_success(
        client.update("/sites/1/attributes/1", required=True),
        {"attribute": {
            "id": 1, "name": "attr1", "description": "",
            "required": True, "site_id": 1, "resource_name": "Network",
            "display": True, "multi": False,
            "constraints": {
                "allow_empty": False,
                "pattern": "",
                "valid_values": []
            }
        }}
    )

    assert_success(
        client.update("/sites/1/attributes/1"),
        {"attribute": {
            "id": 1, "name": "attr1", "description": "",
            "required": False, "site_id": 1, "resource_name": "Network",
            "display": False, "multi": False,
            "constraints": {
                "allow_empty": False,
                "pattern": "",
                "valid_values": []
            }
        }}
    )


def test_deletion(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")
    client.create(
        "/sites/1/attributes",
        resource_name="Network", name="attr1"
    )
    client.create("/sites/1/networks",
        cidr="10.0.0.0/24", attributes={"attr1": "foo"}
    )

    # Don't allow delete when there's an attached network
    assert_error(client.delete("/sites/1/attributes/1"), 409)

    client.delete("/sites/1/networks/1")

    assert_deleted(client.delete("/sites/1/attributes/1"))

