# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in here to access the DB
pytestmark = pytest.mark.django_db

from django.core.urlresolvers import reverse
import logging
from rest_framework import status
from django.conf import settings
import requests

from .fixtures import client
from .util import (
    assert_created, assert_deleted, assert_error, assert_success, TestSite
)


log = logging.getLogger(__name__)

def test_request_xforwardfor(live_server):
    """Test processing of X-Forwarded-For header."""
    url = '{}/api/sites/'.format(live_server.url)
    headers = {
        'X-NSoT-Email': 'gary@localhost',
        'X-Forward-For': '10.1.1.1'
    }

    expected = []

    assert_success(
        requests.get(url, headers=headers),
        expected
    )
