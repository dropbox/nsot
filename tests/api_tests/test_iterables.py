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
    Client, load, filter_iterables, get_result
)

log = logging.getLogger(__name__)

def test_creation(live_server, user, site):
    """ Test Iterable Creation"""
    admin_client = Client(live_server, 'admin')
    user_client = Client(live_server, 'user')

    # URIs
    site_uri = site.list_uri()
    attr_uri = site.list_uri('attribute')
    itr_uri = site.list_uri('iterable')

    admin_client.create(attr_uri, resource_name='Iterable', name='test1')

    
    # Good Creation
    itr_resp = admin_client.create(
        itr_uri, name='test_iterable',
        attributes={'test1': 'foo'},
        min_val=100, max_val=200,
        increment=1,
    )
    
    itr = get_result(itr_resp)
    itr_obj_url = site.detail_uri('iterable', id=itr['id'])
    
    assert_created(itr_resp, itr_obj_url)
    
    # Verify GET all()

    payload = get_result(itr_resp)
    expected = [payload]

    assert_success(admin_client.get(itr_uri), expected)

    # Verify Single Iterable
    assert_success(admin_client.get(itr_obj_url), itr)

    #### Errors ####

    # Permission Error
    assert_error(
        user_client.create(
            itr_uri, name='i_will_fail', 
            min_val=100, max_val=101,
        ),
        status.HTTP_403_FORBIDDEN
    )

    # Bad Attr
    assert_error(
        admin_client.create(
            itr_uri, name='i_will_fail', 
            min_val=100, max_val=101,
            attributes={'test2': 'foo'}
        ),
        status.HTTP_400_BAD_REQUEST
    )