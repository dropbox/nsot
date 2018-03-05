from django.core.urlresolvers import reverse
import json
import logging
import os
import pytest
from pytest_django.fixtures import live_server, django_user_model, settings
import requests

from .util import Client, SiteHelper


log = logging.getLogger(__name__)


# API version to use for the API client
API_VERSION = os.getenv('NSOT_API_VERSION')


@pytest.fixture
def user(django_user_model):
    """Create and return a non-admin user."""
    user = django_user_model.objects.create(email='user@localhost')
    return user


@pytest.fixture
def site(live_server):
    client = Client(live_server)
    site_uri = reverse('site-list')  # /api/sites/
    resp = client.create(site_uri, name='Test Site')

    site = SiteHelper(resp.json())
    return site


@pytest.fixture
def client(live_server):
    """Create and return an admin client."""
    return Client(live_server, api_version=API_VERSION)


@pytest.fixture
def user_client(live_server):
    """Create and return a non-admin client."""
    return Client(live_server, user='user', api_version=API_VERSION)


@pytest.fixture
def nosuperuser_settings(settings):
    """Return settings that have default superuser users disabled."""
    settings.NSOT_NEW_USERS_AS_SUPERUSER = False
    return settings
