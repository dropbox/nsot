import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app, user, session, auth_token
from .util import (
    assert_error, assert_success,
)



def test_no_user(tornado_server):
    assert_error(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port)
    ), 401)


def test_valid_user(tornado_server):
    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={"X-NSoT-Email": "gary@localhost"}
    ), {"sites": [], "limit": None, "offset": 0, "total": 0})


def test_invalid_user(tornado_server):
    assert_error(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={"X-NSoT-Email": "gary"}
    ), 400)


def test_get_auth_token_valid(tornado_server, user):
    """Test that an auth_token can be generated."""
    payload = {"email": user.email, "secret_key": user.secret_key}
    data = json.dumps(payload)
    r = requests.post(
        "http://localhost:{}/api/authenticate".format(tornado_server.port),
        headers={"Content-Type": "application/json"},
        data=data,
    )
    # Since assert_success is checking the payload, we're retreiving and
    # comparing it first.
    response_data = r.json()['data']
    assert_success(r, response_data)


def test_get_auth_token_invalid(tornado_server, user):
    """Test that an auth_token fails w/ a bad secret key."""
    payload = {"email": user.email, "secret_key": "bogus"}
    data = json.dumps(payload)
    assert_error(requests.post(
        "http://localhost:{}/api/authenticate".format(tornado_server.port),
        headers={"Content-Type": "application/json"},
        data=data,
    ), 401)


def test_verify_auth_token_valid(tornado_server, user, auth_token):
    """Test that an auth_token is valid."""
    assert_success(requests.post(
        "http://localhost:{}/api/verify_token".format(tornado_server.port),
        headers={
            "Content-Type": "application/json",
            "Authorization": "AuthToken {}:{}".format(user.email, auth_token)
        },
    ), True)


def test_verify_auth_token_invalid(tornado_server, user):
    """Test that an auth_token is NOT valid."""
    assert_error(requests.post(
        "http://localhost:{}/api/verify_token".format(tornado_server.port),
        headers={
            "Content-Type": "application/json",
            "Authorization": "AuthToken {}:{}".format(user.email, 'bogus')
        },
    ), 401)


def test_valid_auth_token(tornado_server, user, auth_token):
    """Test that a GET can be performed to a resource using auth_token."""
    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={
            "Content-Type": "application/json",
            "Authorization": "AuthToken {}:{}".format(user.email, auth_token)
        },
    ), {"sites": [], "limit": None, "offset": 0, "total": 0})
