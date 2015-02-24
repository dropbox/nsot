import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app, user, session, auth_token
from .util import (
    assert_error, assert_success, Client
)

def test_user_with_secret_key(tornado_server):
    user1_client = Client(tornado_server, "user1")
    user2_client = Client(tornado_server, "user2")

    # Small requests to make user accounts in order.
    user1_client.get("/users/0")
    user2_client.get("/users/0")

    assert_success(
        user1_client.get("/users/0"),
        {"user": {"email": "user1@localhost", "id": 1, "permissions": {}}}
    )

    response = user1_client.get("/users/0?with_secret_key")
    assert_success(
        response,
        {"user": {
            "email": "user1@localhost",
            "id": 1,
            "secret_key": response.json()["data"]["user"]["secret_key"],
            "permissions": {}}
        }
    )

    response = user1_client.get("/users/1?with_secret_key")
    assert_success(
        response,
        {"user": {
            "email": "user1@localhost",
            "id": 1,
            "secret_key": response.json()["data"]["user"]["secret_key"],
            "permissions": {}}
        }
    )

    response = user1_client.get("/users/2?with_secret_key")
    assert_error(response, 403)


def test_user_rotate_secret_key(tornado_server):
    user1_client = Client(tornado_server, "user1")
    user2_client = Client(tornado_server, "user2")

    # Small requests to make user accounts in order.
    user1_client.get("/users/0")
    user2_client.get("/users/0")

    assert_success(user1_client.post("/users/1/rotate_secret_key"))
    assert_error(user1_client.post("/users/2/rotate_secret_key"), 403)
