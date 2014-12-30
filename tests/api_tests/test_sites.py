import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, Client
)


def test_malformed(tornado_server):
    client = Client(tornado_server)
    assert_error(client.post("/sites", user="admin", data="Non-JSON"), 400)


def test_creation(tornado_server):
    client = Client(tornado_server)
    assert_success(client.get("/sites"), {"sites": []})

    assert_created(client.create("/sites", name="Test Site"), "/api/sites/1")
    assert_error(client.create("/sites", name="Test Site"), 409)

    assert_success(
        client.get("/sites"),
        {"sites": [{"description": "", "id": 1, "name": "Test Site"}]}
    )

    assert_success(
        client.get("/sites/1"),
        {"site": {"description": "", "id": 1, "name": "Test Site"}}
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
