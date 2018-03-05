# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in here to access the DB
pytestmark = pytest.mark.django_db

from django.core.urlresolvers import reverse
import logging
from rest_framework import status

from .fixtures import client
from .util import (
    assert_created, assert_deleted, assert_error, assert_success, SiteHelper,
    get_result
)


log = logging.getLogger(__name__)


def test_malformed(client):
    """Test malformed site creation failure."""
    url = reverse('site-list')
    response = client.post(url, data='Non-JSON')

    assert_error(response, status.HTTP_400_BAD_REQUEST)


def test_creation(client):
    """Test creation of Site objects."""
    site_uri = reverse('site-list')

    # We got nothin'!
    expected = []
    assert_success(client.get(site_uri), expected)

    # Create a Site
    site1_resp = client.create(site_uri, name='Test Site')
    site1 = SiteHelper(site1_resp.json())
    site1_obj_uri = site1.detail_uri()
    assert_created(site1_resp, site1_obj_uri)

    # Try (and fail) to create another Site with the same name
    # TODO(jathan): Unique failures might need to be 409 vs. 400?
    assert_error(
        client.create(site_uri, name='Test Site'),
        # status.HTTP_409_CONFLICT
        status.HTTP_400_BAD_REQUEST
    )

    # Create another Site with a slightly different name
    site2_resp = client.create(site_uri, name='Test Site 2')
    site2 = SiteHelper(site2_resp.json())
    site2_obj_uri = site2.detail_uri()
    assert_created(site2_resp, site2_obj_uri)

    # And now retrieve the first Site by name.
    payload = get_result(site1_resp)
    expected = [payload]

    assert_success(
        client.retrieve(site_uri, name='Test Site'),
        expected
    )


def test_update(client):
    """Test update of Site objects."""
    site_uri = reverse('site-list')

    site_resp = client.create(site_uri, name='Test Site')
    site = SiteHelper(site_resp.json())
    site_obj_uri = site.detail_uri()

    # Update the Site name
    params = {'name': 'Test Site 2'}
    expected = get_result(site_resp)
    expected.update(params)

    assert_success(
        client.update(site_obj_uri, **params),
        expected
    )

    # Now add a description and change the name back
    params = {'name': 'Test Site', 'description': 'A description.'}
    expected.update(params)

    assert_success(
        client.update(site_obj_uri, **params),
        expected
    )

    # Try to update with a required field missing (name)
    assert_error(
        client.update(site_obj_uri, description='Only description.'),
        status.HTTP_400_BAD_REQUEST
    )

    # Or an empty payload
    assert_error(client.update(site_obj_uri), status.HTTP_400_BAD_REQUEST)


def test_deletion(client):
    """Test DELETE of Site objects."""
    site_uri = reverse('site-list')
    site_resp = client.create(site_uri, name='Test Site')
    site = SiteHelper(site_resp.json())

    # URIs
    site_obj_uri = site.detail_uri()
    attr_uri = site.list_uri('attribute')
    net_uri = site.list_uri('network')

    # Create a network Attribute
    attr_resp = client.create(attr_uri, resource_name='Network', name='attr1')
    attr = get_result(attr_resp)
    attr_obj_uri = site.detail_uri('attribute', id=attr['id'])

    # Create a Network using that Attribute
    net_resp = client.create(
        net_uri, cidr='10.0.0.0/24', attributes={'attr1': 'foo'}
    )
    net = get_result(net_resp)
    net_obj_uri = site.detail_uri('network', id=net['id'])

    # Don't allow delete when there's an attached network/attribute
    assert_error(client.delete(site_obj_uri), status.HTTP_409_CONFLICT)
    client.delete(net_obj_uri)

    # Stile Don't allow delete when there's an attached attribute
    assert_error(client.delete(site_obj_uri), status.HTTP_409_CONFLICT)
    client.delete(attr_obj_uri)

    # Finally delete.
    assert_deleted(client.delete(site_obj_uri))
