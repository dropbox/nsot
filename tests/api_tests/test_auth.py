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
import requests


from .fixtures import live_server, client, user, site, nosuperuser_settings
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, load, get_result
)


log = logging.getLogger(__name__)


def test_no_user(live_server, site):
    site_uri = site.list_uri()
    url = '{}{}'.format(live_server.url, site_uri)

    assert_error(requests.get(url), status.HTTP_401_UNAUTHORIZED)


def test_valid_user(live_server):
    """Test that a valid user gets through..."""
    url = '{}/api/sites/'.format(live_server.url)
    headers = {'X-NSoT-Email': 'gary@localhost'}
    expected = []

    assert_success(
        requests.get(url, headers=headers),
        expected
    )


def test_invalid_user(live_server):
    """Test that an invalid user DOES NOT get through..."""
    url = '{}/api/sites/'.format(live_server.url)
    headers = {'X-NSoT-Email': 'gary'}

    assert_error(
        requests.get(url, headers=headers),
        status.HTTP_400_BAD_REQUEST
    )


def test_get_auth_token_valid(live_server, user):
    """Test that an auth_token can be generated."""
    auth_uri = reverse('authenticate')
    url = '{}{}'.format(live_server.url, auth_uri)

    headers={'Content-Type': 'application/json'}
    payload = {'email': user.email, 'secret_key': user.secret_key}
    data = json.dumps(payload)

    resp = requests.post(url, headers=headers, data=data)
    expected = get_result(resp)

    # FIXME(jathan): This test is ridiculous. It's testing itself against
    # itself. Of course it will pass! How though? I mean... Yeah.
    assert_success(resp, expected)


def test_get_auth_token_invalid(live_server, user):
    """Test that an auth_token fails w/ a bad secret key."""
    auth_uri = reverse('authenticate')
    url = '{}{}'.format(live_server.url, auth_uri)

    headers={'Content-Type': 'application/json'}
    payload = {'email': user.email, 'secret_key': 'bogus'}
    data = json.dumps(payload)

    assert_error(
        requests.post(url, headers=headers, data=data),
        status.HTTP_401_UNAUTHORIZED
    )


def test_get_auth_token_missing(live_server, user):
    """Test that missing payload results in a 401."""
    auth_uri = reverse('authenticate')
    url = '{}{}'.format(live_server.url, auth_uri)
    headers={'Content-Type': 'application/json'}

    assert_error(
        requests.post(url, headers=headers, data=''),
        status.HTTP_401_UNAUTHORIZED
    )


def test_verify_auth_token_invalid(live_server, user):
    """Test that an auth_token is NOT valid."""
    verify_url = '{}{}'.format(live_server.url, reverse('verify_token'))

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'AuthToken {}:{}'.format(user.email, 'bogus')
    }

    assert_error(
        requests.post(verify_url, headers=headers),
        status.HTTP_400_BAD_REQUEST
    )


def test_verify_auth_token_valid(live_server, site, user):
    """Test that an auth_token is valid."""
    auth_url = '{}{}'.format(live_server.url, reverse('authenticate'))
    verify_url = '{}{}'.format(live_server.url, reverse('verify_token'))

    headers = {'Content-Type': 'application/json'}
    payload = {'email': user.email, 'secret_key': user.secret_key}
    data = json.dumps(payload)

    auth_resp = requests.post(auth_url, headers=headers, data=data)
    auth_token = get_result(auth_resp)['auth_token']

    headers.update({
        'Authorization': 'AuthToken {}:{}'.format(user.email, auth_token)
    })

    assert_success(requests.post(verify_url, headers=headers), True)


def test_valid_auth_token(live_server, user):
    """Test that a GET can be performed to a resource using auth_token."""
    auth_url = '{}{}'.format(live_server.url, reverse('authenticate'))
    site_url = '{}{}'.format(live_server.url, reverse('site-list'))

    headers = {'Content-Type': 'application/json'}
    payload = {'email': user.email, 'secret_key': user.secret_key}
    data = json.dumps(payload)

    auth_resp = requests.post(auth_url, headers=headers, data=data)
    auth_token = get_result(auth_resp)['auth_token']

    headers.update({
        'Authorization': 'AuthToken {}:{}'.format(user.email, auth_token)
    })

    # Allow the user to login to the API
    user.is_staff = True
    user.save()

    # We got nothin'!
    expected = []

    assert_success(
        requests.get(site_url, headers=headers),
        expected
    )


def test_new_users_as_superuser(nosuperuser_settings, live_server, user):
    """Test that settings.NSOT_NEW_USERS_AS_SUPERUSER works."""

    # Assert that new users won't be superuser
    assert not nosuperuser_settings.NSOT_NEW_USERS_AS_SUPERUSER

    # Make the initial user a superuser.
    user.is_superuser = True
    user.save()

    # Data we'll use
    url = '{}/api/sites/'.format(live_server.url)
    new_site = {'name': 'Bogus Site'}
    payload = json.dumps(new_site)

    # This user will be auto-created without superuser and should get a 403.
    headers = {
        'Content-Type': 'application/json',
        'X-NSoT-Email': 'noperms@localhost',
    }

    assert_error(
        requests.post(url, headers=headers, data=payload),
        status.HTTP_403_FORBIDDEN
    )

    # The initial user (w/ superuser) should be cool.
    headers['X-NSoT-Email'] = user.email
    resp = requests.post(url, headers=headers, data=payload)
    assert resp.status_code == status.HTTP_201_CREATED
