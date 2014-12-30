import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success,
    READ_HEADERS, WRITE_HEADERS,
)


def test_no_user(tornado_server):
    assert_error(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port)
    ), 403)


def test_valid_user(tornado_server):
    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers=READ_HEADERS
    ), {"sites": []})


def test_invalid_user(tornado_server):
    assert_error(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={"X-NSoT-Email": "gary"}
    ), 400)
