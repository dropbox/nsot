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
    Client, load, filter_values, get_result
)


log = logging.getLogger(__name__)

def test_creation(client, site):
    """Test creation of an iterable value"""
    #First create the Iterable itr1
    itr_uri = site.list_uri('iterable')
    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
    #Create the first value
    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iter_key=itr['id'], val=nval, u_id='uuid_custA_site1') # create the iterval

    payload = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=payload['id'])
    assert_success(client.get(itrval_obj_uri), payload)

def test_update(client, site):
    """Test PUT  method"""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iter_key=itr['id'], val=nval, u_id='uuid_custA_site1') # create the iterval

    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
    #Update the U_ID
    params =  {'iter_key': itr['id'], 'val': nval, 'u_id': 'new_update' }
    itrval_backup = copy.deepcopy(itrval_resp_dict)
    itrval_backup.update(params)
    assert_success(
            client.update(itrval_obj_uri, **params),
            itrval_backup
            )

    #Reset the object back to it's intital state
    assert_success(
            client.update(itrval_obj_uri, **itrval_resp_dict),
            itrval_resp_dict
            )


 
def test_partial_update(client, site):
    """Test PATCH  method"""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iter_key=itr['id'], val=nval, u_id='uuid_custA_site1') # create the iterval

    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
    #Update the U_ID
    params =  {'u_id': 'new_update' }
    itrval_backup = copy.deepcopy(itrval_resp_dict)
    itrval_backup.update(params)
    assert_success(
            client.partial_update(itrval_obj_uri, **params),
            itrval_backup
            )

def test_deletion(client, site):
    """Test DELETE  method"""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iter_key=itr['id'], val=nval, u_id='uuid_custA_site1') # create the iterval

    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
 

    assert_deleted(client.delete(itrval_obj_uri))
#def test_bulk_operations(client, site):
#    """Test creating/updating multiple Iterables at once."""
#
#    itr_uri = site.list_uri('iterable')
#
#    # Successfully create a collection of Iterables
#    collection = [
#        {'name': 'itr1', 'description': 'iterable1', 'min_val': 10, 'max_val': 20, 'increment': 1},
#        {'name': 'itr2', 'description': 'iterable2', 'min_val': 10, 'max_val': 20, 'increment': 1},
#        {'name': 'itr3', 'description': 'iterable3', 'min_val': 10, 'max_val': 20, 'increment': 1},
#    ]
#    collection_response = client.post(
#        itr_uri,
#        data=json.dumps(collection)
#    )
#    assert_created(collection_response, None)
#
#    # Successfully get all created Attributes
#    output = collection_response.json()
#    cli_resp = client.get(itr_uri)
#    payload = get_result(output)
#
#    assert_success(
#        client.get(itr_uri),
#        payload
#    )
#
