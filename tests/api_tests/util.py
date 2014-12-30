import requests
import json
import urlparse

USERS = {
    "admin": "admin@localhost",
    "user": "gary@localhost",
}
EMAIL_HEADER = "X-NSoT-Email"


def assert_error(response, code):
    output = response.json()
    assert output["status"] == "error"
    assert output["error"]["code"] == code


def assert_success(response, data):
    output = response.json()
    assert output["status"] == "ok"
    assert output["data"] == data


def assert_created(response, location):
    assert response.status_code == 201
    assert response.headers["Location"] == location


class Client(object):
    def __init__(self, tornado_server, user="user"):
        self.tornado_server = tornado_server
        self.user = USERS[user]

    @property
    def base_url(self):
        return "http://localhost:{}/api".format(self.tornado_server.port)

    def request(self, method, url, user="admin", **kwargs):

        headers = {
            EMAIL_HEADER: self.user
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
