from django.core.urlresolvers import reverse
import json
import logging
import pytest
from pytest_django.fixtures import live_server, django_user_model
import requests

from .util import Client, TestSite


log = logging.getLogger(__name__)


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

    site = TestSite(resp.json()['data']['site'])
    return site


@pytest.fixture
def client(live_server):
    return Client(live_server)
