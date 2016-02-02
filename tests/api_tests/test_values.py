# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import copy
from django.core.urlresolvers import reverse
import json
import logging
from rest_framework import status

from .fixtures import live_server, client, user, site
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, load, filter_values
)


log = logging.getLogger(__name__)


def test_filters(site, client):
    """Test field-based filters for Values."""

    # URIs
    attr_uri = site.list_uri('attribute')
    dev_uri = site.list_uri('device')
    val_uri = site.list_uri('value')

    # Pre-load the Attributes
    client.post(attr_uri, data=load('attributes.json'))

    # Populate the Device objects
    client.post(dev_uri, data=load('devices.json'))

    # Get all the Values for testing
    val_resp = client.get(val_uri)
    values_out = val_resp.json()['data']
    values = values_out['values']

    # Test lookup by name
    expected = copy.deepcopy(values_out)
    kwargs = {'name': 'owner'}
    wanted = filter_values(values, **kwargs)
    expected['values'] = wanted
    expected.update({'limit': None, 'offset': 0, 'total': len(wanted)})
    assert_success(
        client.retrieve(val_uri, **kwargs),
        expected
    )

    # Test lookup by name + value
    kwargs = {'name': 'owner', 'value': 'jathan'}
    wanted = filter_values(values, **kwargs)
    expected['values'] = wanted
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(val_uri, **kwargs),
        expected
    )

    # Test lookup by resource_name + resource_id
    kwargs = {'resource_name': 'Device', 'resource_id': 4}
    wanted = filter_values(values, **kwargs)
    expected['values'] = wanted
    expected.update({'total': len(wanted)})
    assert_success(
        client.retrieve(val_uri, **kwargs),
        expected
    )
