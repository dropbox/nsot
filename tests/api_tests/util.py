import json
import os
import requests
import urllib
import urlparse


def _deep_sort(obj):
    if isinstance(obj, dict):
        return {
            key: _deep_sort(value)
            for key, value in obj.iteritems()
        }
    elif isinstance(obj, list):
        return sorted(_deep_sort(elem) for elem in obj)
    return obj


def assert_error(response, code):
    output = response.json()
    assert output["status"] == "error"
    assert output["error"]["code"] == code


def assert_success(response, data=None, ignore_order=True):
    output = response.json()
    assert response.status_code == 200
    assert output["status"] == "ok"
    if data is not None:
        print 'OUTPUT DATA = %r' % (output['data'],)
        print 'QUERY DATA = %r' % (data,)
        if ignore_order:
            assert _deep_sort(output["data"]) == _deep_sort(data)
        else:
            assert output["data"] == data


def assert_created(response, location, data=None):
    output = response.json()
    assert response.status_code == 201
    assert response.headers.get("Location") == location
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


def load_json(relpath):
    """
    Load JSON files relative to this directory.

    Files are loaded from the 'data' directory. So for example for
    ``/path/to/data/devices/foo.json`` the ``relpath`` would be
    ``devices/foo.json``.

    :param relpath:
        Relative path to our directory's "data" dir
    """
    our_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(our_path, 'data')
    filepath = os.path.join(data_dir, relpath)
    with open(filepath, 'rb') as f:
        return json.load(f)


def run_set_queries(resource_name, client, device_queries):
    """
    Run set queries on the specified resource.

    The directory structure is expected to match the resource path. So
    "devices/query" would map to both the data directory for JSON response
    files, and the API URL of "/api/sites/1/devices/query".

    The ``device_queries is expected to be a list of 2-tuples of (query,
    filename) where query is a set query and filename is a file containing the
    expected response JSON. Example::

        [
            ('foo=bar', 'test1.json'),
            ('bar=baz', 'test2.json'),
        ]

    :param resource_name:
        The resource for which to run query tests

    :param client:
        A ``Client`` instance

    :param devices_queries:
        A list of 2-tuples of (query, filename)
    """
    base_path = '/sites/1'
    path = os.path.join(resource_name, 'query')
    base_uri = os.path.join(base_path, path)
    uri = base_uri + '?query='  # '/sites/1/devices/query?query='

    # Walk the query and filename, construct a URL w/ the query, load up the
    # file, call the URL w/ the client, and compare the return data to the
    # loaded data.
    for query, filename in device_queries:
        qs = urllib.quote_plus(query)  # 'foo=bar' => 'foo%3Dbar'
        url = uri + qs  # => /sites/1/devices/query?query=foo%3Dbar
        filepath = os.path.join(path, filename)  # devices/query/query1.json
        output = load_json(filepath)
        assert_success(
            client.get(url),
            output['data']
        )
