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


def test_user_with_secret_key(live_server):
    user1_client = Client(live_server, 'user1')
    user2_client = Client(live_server, 'user2')

    # URI for user 0
    user_uri = reverse('user-detail', args=(0,))

    # Small requests to make user accounts in order.
    user1_resp = user1_client.get(user_uri)
    user1 = get_result(user1_resp)
    user1_uri = reverse('user-detail', args=(user1['id'],))

    user2_resp = user2_client.get(user_uri)
    user2 = get_result(user2_resp)
    user2_uri = reverse('user-detail', args=(user2['id'],))

    # User should be able to get user 0 (self)
    assert_success(
        user1_client.get(user_uri),
        user1
    )

    # And see their own secret key as user 0
    response = user1_client.get(user_uri + '?with_secret_key')
    expected = copy.deepcopy(user1)
    result = get_result(response)
    expected['secret_key'] = result['secret_key']
    assert_success(response, expected)

    # And their own secret key by their user id 
    response = user1_client.get(user1_uri + '?with_secret_key')
    assert_success(response, expected)

    # But not user 2's secret_key.
    response = user1_client.get(user2_uri + '?with_secret_key')
    assert_error(response, status.HTTP_403_FORBIDDEN)


def test_user_rotate_secret_key(live_server):
    user1_client = Client(live_server, 'user1')
    user2_client = Client(live_server, 'user2')

    # URI for user 0
    user_uri = reverse('user-detail', args=(0,))

    # Small requests to make user accounts in order.
    user1_resp = user1_client.get(user_uri)
    user1 = get_result(user1_resp)
    user1_key_uri = reverse('user-rotate-secret-key', args=(user1['id'],))

    user2_resp = user2_client.get(user_uri)
    user2 = get_result(user2_resp)
    user2_key_uri = reverse('user-rotate-secret-key', args=(user2['id'],))

    # User1 should be able to rotate their own secret_key
    assert_success(user1_client.post(user1_key_uri))

    # But not user 2's secret_key
    assert_error(user1_client.post(user2_key_uri), status.HTTP_403_FORBIDDEN)
