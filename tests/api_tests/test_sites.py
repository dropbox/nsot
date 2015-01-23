import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, assert_deleted, Client
)


def test_malformed(tornado_server):
    client = Client(tornado_server)
    assert_error(client.post("/sites", user="admin", data="Non-JSON"), 400)


def test_creation(tornado_server):
    client = Client(tornado_server)
    assert_success(client.get("/sites"), {
        "sites": [],
        "limit": None,
        "offset": 0,
        "total": 0,
    })

    assert_created(client.create("/sites", name="Test Site"), "/api/sites/1")
    assert_error(client.create("/sites", name="Test Site"), 409)

    assert_success(
        client.get("/sites"),
        {
            "sites": [{"description": "", "id": 1, "name": "Test Site"}],
            "limit": None,
            "offset": 0,
            "total": 1,
        }
    )

    assert_success(
        client.get("/sites/1"),
        {"site": {"description": "", "id": 1, "name": "Test Site"}}
    )

    assert_created(client.create("/sites", name="Test Site 2"), "/api/sites/2")
    assert_success(
        client.get("/sites", params={"name": "Test Site"}),
        {
            "sites": [{"description": "", "id": 1, "name": "Test Site"}],
            "limit": None,
            "offset": 0,
            "total": 1,
        }
    )


def test_update(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")

    assert_success(
        client.update("/sites/1", name="Test Site 2"),
        {"site": {"description": "", "id": 1, "name": "Test Site 2"}}
    )

    assert_success(
        client.update("/sites/1", name="Test Site", description="A description."),
        {"site": {"description": "A description.", "id": 1, "name": "Test Site"}}
    )

    assert_error(client.update("/sites/1", description="Only description."), 400)
    assert_error(client.update("/sites/1"), 400)


def test_deletion(tornado_server):
    client = Client(tornado_server)

    client.create("/sites", name="Test Site")
    client.create("/sites/1/attributes", resource_name="Network", name="attr1")
    client.create("/sites/1/networks",
        cidr="10.0.0.0/24", attributes={"attr1": "foo"}
    )

    # Don't allow delete when there's an attached network/attribute
    assert_error(client.delete("/sites/1"), 409)

    client.delete("/sites/1/networks/1")

    # Stile Don't allow delete when there's an attached attribute
    assert_error(client.delete("/sites/1"), 409)

    client.delete("/sites/1/attributes/1")

    assert_deleted(client.delete("/sites/1"))
