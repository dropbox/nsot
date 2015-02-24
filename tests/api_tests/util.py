import requests
import json
import urlparse


def assert_error(response, code):
    output = response.json()
    assert output["status"] == "error"
    assert output["error"]["code"] == code


def assert_success(response, data=None):
    output = response.json()
    assert response.status_code == 200
    assert output["status"] == "ok"
    if data is not None:
        assert output["data"] == data


def assert_created(response, location, data=None):
    output = response.json()
    assert response.status_code == 201
    assert response.headers["Location"] == location
    assert output["status"] == "ok"
    if data is not None:
        assert output["data"] == data


def assert_deleted(response):
    output = response.json()
    assert response.status_code == 200
    assert output["status"] == "ok"


class Client(object):
    def __init__(self, tornado_server, user="user"):
        self.tornado_server = tornado_server
        self.user = "{}@localhost".format(user)

    @property
    def base_url(self):
        return "http://localhost:{}/api".format(self.tornado_server.port)

    def request(self, method, url, user="admin", **kwargs):

        headers = {
            "X-NSoT-Email": self.user
        }

        if method.lower() in ("put", "post"):
            headers["Content-type"] = "application/json"

        return requests.request(
            method, self.base_url + url,
            headers=headers, **kwargs
        )

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def create(self, url, **kwargs):
        return self.post(url, data=json.dumps(kwargs))

    def update(self, url, **kwargs):
        return self.put(url, data=json.dumps(kwargs))
