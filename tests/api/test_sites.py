import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import assert_error, assert_success, assert_created


def test_creation(tornado_server):
    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={"X-NSoT-Email": "gary@localhost"}
    ), {"sites": []})

    assert_created(requests.post(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={
            "X-NSoT-Email": "gary@localhost",
            "Content-type": "application/json",
        }, data=json.dumps({
            "name": "Test Site"
        })
    ), "/api/sites/1")

    assert_success(requests.get(
        "http://localhost:{}/api/sites".format(tornado_server.port),
        headers={"X-NSoT-Email": "gary@localhost"}
    ), {"sites": [{u"description": u"", u"id": 1, u"name": u"Test Site"}]})

    assert_success(requests.get(
        "http://localhost:{}/api/sites/1".format(tornado_server.port),
        headers={"X-NSoT-Email": "gary@localhost"}
    ), {"site": {u"description": u"", u"id": 1, u"name": u"Test Site"}})
