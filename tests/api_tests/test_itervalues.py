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

    #Create the attribute
    attr_uri = site.list_uri('attribute')
    client.create(attr_uri, resource_name='Itervalue', name='service_key')

    #Create the first value
    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr['id'], value=nval, attributes={'service_key': 'custA01_key1'}) # create the iterval

    payload = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=payload['id'])
    assert_success(client.get(itrval_obj_uri), payload)

def test_filters(site, client):
    """Test attribute filter for Itervalue"""
    itr_uri = site.list_uri('iterable')
    itr_resp1 = client.create(itr_uri, name='itr1', description="test-iterable1", min_val=10, max_val=20, increment=1)
    itr1 = get_result(itr_resp1)
    itr_resp2 = client.create(itr_uri, name='itr2', description="test-iterable2", min_val=100, max_val=200, increment=1)
    itr2 = get_result(itr_resp2)

    #Create the attribute
    attr_uri = site.list_uri('attribute')
    client.create(attr_uri, resource_name='Itervalue', name='service_key')
    #### create itervalues for itr1
    #create the first value
    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custa01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custa01_key2'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custb01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custb01_key2'}) # create the iterval
    #### create itervalues for itr2
    #create the first value
    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custa01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custa01_key2'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custb01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custb01_key2'}) # create the iterval


    #Test lookup by attribute
    expected = [ 12, 102 ] #Values assigned to custb01_key1
    returned = get_result(client.retrieve(itrval_uri, attributes='service_key=custb01_key1'))
    result = [ val['value'] for val in returned ]
    assert result == expected



def test_update(client, site):
    """Test PUT  method"""
    itr_uri = site.list_uri('iterable')

    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
    itr = get_result(itr_resp)
 
    #Create the attribute
    attr_uri = site.list_uri('attribute')
    client.create(attr_uri, resource_name='Itervalue', name='service_key')


    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr['id'], value=nval, attributes={'service_key': 'custA01_key1'}) # create the iterval

    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
    #Update the attribute
    params =  {'iterable': itr['id'], 'value': nval, 'attributes': {'service_key': 'UPDATED'} }
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
    #Create the attribute
    attr_uri = site.list_uri('attribute')
    client.create(attr_uri, resource_name='Itervalue', name='service_key')

    itrval_uri = site.list_uri('itervalue')
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr['id'], value=nval, attributes={'service_key': 'custA01_key1'}) # create the iterval

    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
    #Update the U_ID
    params =  {'attributes': {'service_key': 'UPDATED'}}
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
 
    #Create the attribute
    attr_uri = site.list_uri('attribute')
    client.create(attr_uri, resource_name='Itervalue', name='service_key')
    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])

    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue

    itrval_resp = client.create(itrval_uri, iterable=itr['id'], value=nval, attributes={'service_key': 'custA01_key1'}) # create the iterval
    itrval_resp_dict = get_result(itrval_resp)
    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
 

    assert_deleted(client.delete(itrval_obj_uri))

def test_skey_deletion(client, site):
    """Test deletion of multiple itervalues based on the service key attribute"""

    itr_uri = site.list_uri('iterable')
    itr_resp1 = client.create(itr_uri, name='itr1', description="test-iterable1", min_val=10, max_val=20, increment=1)
    itr1 = get_result(itr_resp1)
    itr_resp2 = client.create(itr_uri, name='itr2', description="test-iterable2", min_val=100, max_val=200, increment=1)
    itr2 = get_result(itr_resp2)

    #Create the attribute
    attr_uri = site.list_uri('attribute')
    client.create(attr_uri, resource_name='Itervalue', name='service_key')
    #### create itervalues for itr1
    #create the first value
    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custa01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custa01_key2'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custb01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr1['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr1['id'], value=nval, attributes={'service_key': 'custb01_key2'}) # create the iterval
    #### create itervalues for itr2
    #create the first value
    itrval_uri = site.list_uri('itervalue')
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custa01_key1'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custa01_key2'}) # create the iterval
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custb01_key1'}) # create the iterval 1 
    #create the next value
    nval = client.get(reverse('iterable-next-value', args=(site.id, itr2['id']))).json()[0] #get the next value to assign to the itervalue
    itrval_resp = client.create(itrval_uri, iterable=itr2['id'], value=nval, attributes={'service_key': 'custb01_key2'}) # create the iterval


    #Test lookup by attribute
    expected = [ 12, 102 ] #Values assigned to custb01_key1
    returned = get_result(client.retrieve(itrval_uri, attributes='service_key=custb01_key1'))
    for iv in returned:
        ival_uri = site.detail_uri('itervalue', id=iv['id'])
        client.delete(ival_uri)

    #Assert that all values associate with custb, key1 are gone, but cust b key1 is still around
    assert get_result(client.retrieve(itrval_uri, attributes='service_key=custb01_key1')) == []
    custb_key2 =  get_result(client.retrieve(itrval_uri, attributes='service_key=custb01_key2'))
    result = [ val['value'] for val in custb_key2 ]
    assert result == [13, 103]

   
#    """Test DELETE  method"""
#    itr_uri = site.list_uri('iterable')
#
#    itr_resp = client.create(itr_uri, name='itr1', description="test-iterable", min_val=10, max_val=20, increment=1)
#    itr = get_result(itr_resp)
# 
#    #Create the attribute
#    attr_uri = site.list_uri('attribute')
#    client.create(attr_uri, resource_name='Itervalue', name='service_key')
#    itr_pk_uri = site.detail_uri('iterable', id=itr['id'])
#
#    itrval_uri = site.list_uri('itervalue')
#    nval = client.get(reverse('iterable-next-value', args=(site.id, itr['id']))).json()[0] #Get the next value to assign to the itervalue
#
#    itrval_resp = client.create(itrval_uri, iterable=itr['id'], value=nval, attributes={'service_key': 'custA01_key1'}) # create the iterval
#    itrval_resp_dict = get_result(itrval_resp)
#    itrval_obj_uri = site.detail_uri('itervalue', id=itrval_resp_dict['id'])
# 
#
#    assert_deleted(client.delete(itrval_obj_uri))
#
