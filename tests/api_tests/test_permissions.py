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
    admin_client.create("/sites/1/attributes", resource_name="Network", name="attr1")
    admin_client.create("/sites/1/networks", cidr="10.0.0.0/24")

    user_client.get("/")  # Just create user id 2

    assert_success(
        user_client.get("/users/1/permissions"),
        {"permissions": {"1": {"permissions": ["admin"], "site_id": 1, "user_id": 1}}}
    )

    assert_success(
        admin_client.get("/users/1/permissions/1"),
        {"permission": {"permissions": ["admin"], "site_id": 1, "user_id": 1}}
    )

    # Explicitly Set permissions for user_client to have none.
    assert_success(admin_client.update(
        "/users/2/permissions/1", permissions=[]
    ),
        {"permission": {"permissions": [], "site_id": 1, "user_id": 2}}
    )

    # User shouldn't be able to update site or create/update other resources
    assert_error(
        user_client.update("/sites/1", name="attr1"),
        403
    )
    assert_error(
        user_client.create("/sites/1/attributes", name="attr2"),
        403
    )
    assert_error(
        user_client.update("/sites/1/attributes/1", required=True),
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
