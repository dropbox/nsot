import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created,
    READ_HEADERS, WRITE_HEADERS,
)

def _create_site(tornado_server):
    return requests.post(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers=WRITE_HEADERS,
        data=json.dumps({
            "name": "Test Site"
        })
    )

def test_creation(tornado_server):
    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers=READ_HEADERS
    ), {"sites": []})

    assert_created(_create_site(tornado_server), "/api/sites/1")

    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers=READ_HEADERS
    ), {"sites": [{u"description": u"", u"id": 1, u"name": u"Test Site"}]})

    assert_success(requests.get(
        "http://localhost:{}/api/sites/1".format(tornado_server.port),
        headers=READ_HEADERS
    ), {"site": {u"description": u"", u"id": 1, u"name": u"Test Site"}})


def test_update(tornado_server):
    _create_site(tornado_server)

    assert_success(requests.put(
        "http://localhost:{}/api/sites/1".format(tornado_server.port),
        headers=WRITE_HEADERS,
        data=json.dumps({
            "name": "Test Site 2",
        })
    ), {"site": {u"description": u"", u"id": 1, u"name": u"Test Site 2"}})


    assert_success(requests.put(
        "http://localhost:{}/api/sites/1".format(tornado_server.port),
        headers=WRITE_HEADERS,
        data=json.dumps({
            "name": "Test Site",
            "description": "A description.",
        })
    ), {"site": {u"description": u"A description.", u"id": 1, u"name": u"Test Site"}})

    assert_error(requests.put(
        "http://localhost:{}/api/sites/1".format(tornado_server.port),
        headers=WRITE_HEADERS,
        data=json.dumps({
            "description": "Only description without name.",
        })
    ), 400)
