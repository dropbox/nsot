import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, assert_deleted, Client
)


def test_permissions(tornado_server):
    admin_client = Client(tornado_server, "admin")
    user_client = Client(tornado_server, "user")

    admin_client.create("/sites", name="Test Site")
    admin_client.create("/sites/1/network_attributes", name="attr1")
    admin_client.create("/sites/1/networks", cidr="10.0.0.0/24")

    user_client.get("/")  # Just create user id 2

    assert_success(
        user_client.get("/users/1/permissions"),
        {"permissions": [{'permissions': 1, 'site_id': 1, 'user_id': 1}]}
    )

    assert_success(
        admin_client.get("/users/1/permissions/1"),
        {"permission": {'permissions': 1, 'site_id': 1, 'user_id': 1}}
    )

    # Explicitly Set permissions for user_client to have none.
    assert_success(admin_client.update(
        "/users/2/permissions/1", permissions=0
    ),
        {"permission": {'permissions': 0, 'site_id': 1, 'user_id': 2}}
    )

    # User shouldn't be able to update site or create/update other resources
    assert_error(
        user_client.update("/sites/1", name="attr1"),
        403
    )
    assert_error(
        user_client.create("/sites/1/network_attributes", name="attr2"),
        403
    )
    assert_error(
        user_client.update("/sites/1/network_attributes/1", required=True),
        403
    )
    assert_error(
        user_client.create("/sites/1/networks", cidr="10.0.0.0/8"),
        403
    )
    assert_error(
        user_client.update("/sites/1/networks/1", attributes={"attr1": "foo"}),
        403
    )

    # Update permissions to have network_attrs perms
    admin_client.update("/users/2/permissions/1", permissions=4)
    assert_error(
        user_client.update("/sites/1", name="attr1"),
        403
    )
    assert_created(
        user_client.create("/sites/1/network_attributes", name="attr2"),
        "/api/sites/1/network_attributes/2"
    )
    assert_success(
        user_client.update("/sites/1/network_attributes/2", required=True),
        {"network_attribute": {
            "id": 2, "name": "attr2", "description": "",
            "required": True, "site_id": 1,
        }}
    )
    assert_error(
        user_client.create("/sites/1/networks", cidr="10.0.0.0/8"),
        403
    )
    assert_error(
        user_client.update("/sites/1/networks/1", attributes={"attr1": "foo"}),
        403
    )

    # Update permissions to have network perms
    admin_client.update("/users/2/permissions/1", permissions=2)
    assert_error(
        user_client.update("/sites/1", name="attr1"),
        403
    )
    assert_error(
        user_client.create("/sites/1/network_attributes", name="attr2"),
        403
    )
    assert_error(
        user_client.update("/sites/1/network_attributes/1", required=True),
        403
    )
    assert_created(
        user_client.create(
            "/sites/1/networks",
            cidr="10.0.0.0/8",
            attributes={"attr2": "foo"}
        ),
        "/api/sites/1/networks/2"
    )
    assert_success(
        user_client.update("/sites/1/networks/2", attributes={"attr2": "bar"}),
        {"network": {
            "attributes": {"attr2": "bar"},
            "id": 2,
            "ip_version": "4",
            "is_ip": False,
            "network_address": "10.0.0.0",
            "prefix_length": 8,
            "site_id": 1
        }}
    )
