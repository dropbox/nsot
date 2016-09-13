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
    Client, load, get_result
)


log = logging.getLogger(__name__)


def test_creation(client, site):
    """Test creation of Attributes."""

    attr_uri = site.list_uri('attribute')

    # Test invalid attribute name
    assert_error(
        client.create(
            attr_uri,
            resource_name='Network', name='invalid attr1'
        ),
        status.HTTP_400_BAD_REQUEST
    )

    # Successfully create an Attribute
    attr_resp = client.create(attr_uri, resource_name='Network', name='attr1')
    attr = get_result(attr_resp)
    attr_obj_uri = site.detail_uri('attribute', id=attr['id'])
    assert_created(attr_resp, attr_obj_uri)

    # Successfully get all Network Attributes
    payload = get_result(attr_resp)
    expected = [payload]
    assert_success(client.get(attr_uri), expected)

    # Successfully get a single Network Attribute
    assert_success(client.get(attr_obj_uri), payload)


def test_bulk_operations(client, site):
    """Test creating/updating multiple Attributes at once."""

    attr_uri = site.list_uri('attribute')

    # Successfully create a collection of Attributes
    collection = [
        {'name': 'attr1', 'resource_name': 'Network'},
        {'name': 'attr2', 'resource_name': 'Network'},
        {'name': 'attr3', 'resource_name': 'Network'},
    ]
    collection_response = client.post(
        attr_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Attributes
    output = collection_response.json()
    payload = get_result(output)

    assert_success(
        client.get(attr_uri),
        payload
    )

    # Test bulk update to add a description to each Attribute
    updated = copy.deepcopy(payload)

    for item in updated:
        item['description'] = 'This is the best attribute ever.'
    updated_resp = client.put(attr_uri, data=json.dumps(updated))
    expected = updated_resp.json()

    assert updated == expected


def test_update(client, site):
    """Test updating Attributes w/ PUT."""

    attr_uri = site.list_uri('attribute')

    attr_resp = client.create(attr_uri, resource_name='Network', name='attr1')
    attr = get_result(attr_resp)
    attr_obj_uri = site.detail_uri('attribute', id=attr['id'])

    # Update the description
    params = {'description': 'Attribute 1'}
    attr1 = copy.deepcopy(attr)
    attr1.update(params)

    assert_success(
        client.update(attr_obj_uri, **params),
        attr1
    )

    # Update the required flag; which should also set display=True
    params = {'required': True}
    attr2 = copy.deepcopy(attr1)
    attr2.update(params)
    attr2['display'] = True

    assert_success(
        client.update(attr_obj_uri, **params),
        attr2
    )

    # Reset the object back to it's initial state!
    assert_success(
        client.update(attr_obj_uri, **attr),
        attr
    )


def test_partial_update(site, client):
    """Test PATCH operations to partially update an Attribute."""
    attr_uri = site.list_uri('attribute')

    attr_resp = client.create(attr_uri, resource_name='Network', name='attr1')
    attr = get_result(attr_resp)
    attr_pk_uri = site.detail_uri('attribute', id=attr['id'])

    # Update display
    params = {'display': True}
    payload = copy.deepcopy(attr)
    payload.update(params)

    assert_success(
        client.partial_update(attr_pk_uri, **params),
        payload
    )

    # Update constraints
    params = {
        u'constraints': {
            u'allow_empty': True, u'pattern': u'', u'valid_values': []
        }
    }
    payload.update(params)
    assert_success(
        client.partial_update(attr_pk_uri, **params),
        payload
    )


def test_deletion(client, site):
    """Test DELETE operations for Attributes."""

    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    attr_resp = client.create(attr_uri, resource_name='Network', name='attr1')
    attr = get_result(attr_resp)
    attr_obj_uri = site.detail_uri('attribute', id=attr['id'])

    # Create a Network with an attribute
    net_resp = client.create(
        net_uri, cidr='10.0.0.0/24', attributes={'attr1': 'foo'}
    )
    net = get_result(net_resp)

    net_obj_uri = site.detail_uri('network', id=net['id'])

    # Don't allow delete when there's an attached network
    assert_error(
        client.delete(attr_obj_uri),
        status.HTTP_409_CONFLICT
    )

    # Now delete the Network
    client.delete(net_obj_uri)

    # And safely delete the Attribute
    assert_deleted(client.delete(attr_obj_uri))
