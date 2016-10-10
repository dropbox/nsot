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
    """Test creation of Iterables."""

    itr_uri = site.list_uri('iterable')
    # Successfully create an iterable
    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
    itr_obj_uri = site.detail_uri('iterable', id=itr['id'])
    assert_created(itr_resp, itr_obj_uri)

    #Validate that the repsonse (which contains the creation data) matches the GET response, upon quering the API
    payload = get_result(itr_resp)
    expected = [payload]
    get_resp = client.get(itr_uri)
    assert_success(client.get(itr_uri), expected)
    # Successfully get a single Network Attribute
    assert_success(client.get(itr_obj_uri), payload)

    # Verify successful get of single Iterable  by natural_key
    itr_natural_uri = site.detail_uri('iterable', id='itr1')
    assert_success(client.get(itr_natural_uri), itr)
def test_bulk_operations(client, site):
    """Test creating/updating multiple Iterables at once."""

    itr_uri = site.list_uri('iterable')

    # Successfully create a collection of Iterables
    collection = [
        {'name': 'itr1', 'description': 'iterable1', 'min_val': 10, 'max_val': 20, 'increment': 1},
        {'name': 'itr2', 'description': 'iterable2', 'min_val': 10, 'max_val': 20, 'increment': 1},
        {'name': 'itr3', 'description': 'iterable3', 'min_val': 10, 'max_val': 20, 'increment': 1},
    ]
    collection_response = client.post(
        itr_uri,
        data=json.dumps(collection)
    )
    assert_created(collection_response, None)

    # Successfully get all created Attributes
    output = collection_response.json()
    cli_resp = client.get(itr_uri)
    payload = get_result(output)

    assert_success(
        client.get(itr_uri),
        payload
    )

    # Test bulk update to add a description to each Attribute
#    updated = copy.deepcopy(payload)
#
#    for item in updated:
#        item['description'] = 'This is the best attribute ever.'
#    updated_resp = client.put(itr_uri, data=json.dumps(updated))
#    expected = updated_resp.json()
#
#    assert updated == expected

#
def test_update(client, site):
    """Test updating Attributes w/ PUT."""

    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_obj_uri = site.detail_uri('iterable', id=itr['id'])
#    # Update the description
    params = {'description': 'Iterable 1', 'id': itr['id'], 'name': itr['name'], 'min_val': itr['min_val'], 'max_val': itr['max_val'] }
    itr1 = copy.deepcopy(itr)
    itr1.update(params)

    client.update(itr_obj_uri, **params),
    assert_success(
        client.update(itr_obj_uri, **params),
        itr1
    )

    # Reset the object back to it's initial state!
    assert_success(
        client.update(itr_obj_uri, **itr),
        itr
    )


def test_partial_update(site, client):
    """Test PATCH operations to partially update an Iterable."""

    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    # Update display
    params = {'description': 'Iterable 1'}
    payload = copy.deepcopy(itr)
    payload.update(params)

    assert_success(
        client.partial_update(itr_pk_uri, **params),
        payload
    )

    
def test_getnext(client, site):
    """ Test that the next value for the iterable is returned"""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    uri = reverse('iterable-next-value', args=(site.id, itr['id']))

    expected = [10] # Minimum val is offered up, since no other values are assigned

    assert client.get(uri).json() == expected

   
def test_deletion(client, site):
    """Test DELETE operations for Iterable."""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])
    assert_deleted(client.delete(itr_pk_uri))

def test_del_protect(client, site):
    """Test DELETE Protection operations for Iterable."""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr['id'], value=nval, unique_id='uuid_custA_site1') # create the iterval

    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
    # Don't allow delete when there's a value associated
    assert_error(
        client.delete(itr_pk_uri),
        status.HTTP_409_CONFLICT
    )

    # Now delete the Value
    client.delete(itrval_obj_uri)

    # And safely delete the Iterable
    assert_deleted(client.delete(itr_pk_uri))



