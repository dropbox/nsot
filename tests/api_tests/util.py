"""
Utilities for unit-testsing of API endpoints.
"""

from hashlib import sha1
import json
import os
from urlparse import urlparse

from django.core.urlresolvers import reverse
import macaddress
import netaddr
from rest_framework import status
import requests


'''
__all__ = (
    'get_result', 'assert_error', 'assert_success', 'assert_created',
    'assert_deleted', 'Client', 'SiteHelper', 'load_json', 'load',
    'filter_devices', 'filter_interfaces', 'filter_networks', 'filter_values',
    'filter_circuits', 'make_mac', 'mkcidr',
)
'''


def _deep_sort(obj):
    """Sort the items in an object so comparisons succeed."""
    if isinstance(obj, dict):
        return {
            key: _deep_sort(value)
            for key, value in obj.iteritems()
        }
    elif isinstance(obj, list):
        return sorted(_deep_sort(elem) for elem in obj)
    return obj


def get_result(response):
    """
    Get the desired result from an API response.

    :param response:
        Requests API response object
    """
    try:
        payload = response.json()
    except AttributeError:
        payload = response

    # If it's a Bool, return it.
    if payload in (True, False):
        return payload

    elif 'results' in payload:
        return payload['results']

    # Or just return the payload... (next-gen)
    return payload


def assert_error(response, code):
    """Assert a response resulted in an error."""
    output = response.json()
    assert output['error']['code'] == code


def assert_success(response, data=None, ignore_order=True):
    """Assert a response resulted in an success."""
    output = get_result(response)
    assert response.status_code == status.HTTP_200_OK

    if data is not None:

        print 'OUTPUT_DATA = %r' % (output,)
        print 'EXPECTED_DATA = %r' % (data,)
        if ignore_order:
            assert _deep_sort(output) == _deep_sort(data)
        else:
            assert output == data


def assert_created(response, location, data=None):
    """Assert 201 CREATED."""
    output = get_result(response)
    assert response.status_code == status.HTTP_201_CREATED

    resp_location = response.headers.get('Location')
    if resp_location is not None:
        url = urlparse(resp_location)
        resp_location = url.path

    assert resp_location == location

    if data is not None:
        assert output == data


def assert_deleted(response):
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # TODO(jathan): If we want the deleted object to be returned, then this
    # test will have to be updated.
    # output = response.json()
    # assert output["status"] == "ok"


class Client(object):
    def __init__(self, live_server, user="admin", api_version=None):
        self.live_server = live_server
        self.user = "{}@localhost".format(user)
        self.session = requests.Session()
        self.api_version = api_version

    @property
    def base_url(self):
        return self.live_server.url

    def request(self, method, url, user="admin", **kwargs):

        headers = {
            "X-NSoT-Email": self.user,
        }

        # If api_version is set, let's use that.
        api_version = kwargs.get('api_version', self.api_version)
        if api_version is not None:
            headers["Accept"] = "*/*; version=%s" % api_version

        # If we're updating/creating, set content-type to json
        if method.lower() in ("put", "post", "patch"):
            headers["Content-type"] = "application/json"

        # Record stuff w/ Betamax for some reason.
        from betamax import Betamax
        cassette = sha1(url).hexdigest()  # SHA1 the URI!
        with Betamax(self.session).use_cassette(cassette):
            return self.session.request(
                method, self.base_url + url,
                headers=headers, **kwargs
            )

        '''
        return self.session.request(
            method, self.base_url + url,
            headers=headers, **kwargs
        )
        '''

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)

    def create(self, url, **kwargs):
        return self.post(url, data=json.dumps(kwargs))

    def update(self, url, **kwargs):
        return self.put(url, data=json.dumps(kwargs))

    def partial_update(self, url, **kwargs):
        return self.patch(url, data=json.dumps(kwargs))

    def retrieve(self, url, **kwargs):
        return self.get(url, params=kwargs)

    def destroy(self, url, **kwargs):
        return self.delete(url, params=kwargs)


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


def load(relpath):
    our_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(our_path, 'data')
    filepath = os.path.join(data_dir, relpath)
    with open(filepath, 'rb') as f:
        return f.read()


def filter_devices(devices, wanted):
    """
    Return a list of desired Device objects.

    :param devices:
        list of Device dicts

    :param wanted:
        list of hostnames you want
    """
    return [d for d in devices if d['hostname'] in wanted]


def filter_interfaces(interfaces, wanted):
    """
    Return a list of desired Interface objects.

    :param interfaces:
        list of Interface dicts

    :param name:
        list of Interface objects you want
    """
    return [i for i in interfaces if i in wanted]


def filter_circuits(circuits, wanted):
    """
    Return a list of desired Circuit objects.

    :param circuits:
        list of Circuit dicts

    :param name:
        list of Circuit objects you want
    """
    return [c for c in circuits if c in wanted]


def filter_networks(networks, wanted):
    """
    Return a list of desired Network objects.

    :param networks:
        list of Network dicts

    :param wanted:
        list of cidrs you want
    """
    return [
        n for n in networks if '%s/%s' % (
            n['network_address'], n['prefix_length']
        ) in wanted
    ]


def filter_values(values, **wanted):
    """
    Return a list of desired Value objects.

    :param networks:
        list of Value dicts

    :param wanted:
        kwargs of field/value to filter on
    """
    ret = []
    for v in values:
        if all(v.get(field) == value for field, value in wanted.items()):
            ret.append(v)

    return ret


def make_mac(mac):
    """
    Return a MAC address in the default dialect.

    :param mac:
        MAC address (string, integer, or EUI object)
    """
    return netaddr.EUI(mac, dialect=macaddress.default_dialect())


class SiteHelper(object):
    """Class used to help with common API things in testing."""
    def __init__(self, data):
        if 'data' in data:
            data = data['data']['site']
        self._data = data
        self.__dict__.update(**data)

    def list_uri(self, name=None, site_id=None):
        """Return a list URL like /api/sites/ or /api/sites/1/devices/"""
        args = []
        if name is None:
            name = 'site'

        if site_id is None:
            site_id = self.id

        if site_id and name != 'site':
            args.append(site_id)

        return reverse(name + '-list', args=args)

    def detail_uri(self, name=None, site_id=None, id=None):
        """Return a detail URL like /api/sites/1/ or /api/sites/1/devices/1/"""
        if name is None:
            name = 'site'

        if site_id is None:
            site_id = self.id
        args = [site_id]

        if id is not None:
            args.append(id)

        return reverse(name + '-detail', args=args)

    def query_uri(self, name, site_id=None):
        """Return a query URL like /api/sites/1/devices/query/"""
        if site_id is None:
            site_id = self.id
        args = [site_id]

        return reverse(name + '-query', args=args)

    def __repr__(self):
        return '<SiteHelper: %s (%s)>' % (self.name, self.id)


def mkcidr(obj):
    """
    Return cidr-formatted string.

    :param obj:
        Dict of an object
    """
    return '%s/%s' % (obj['network_address'], obj['prefix_length'])
