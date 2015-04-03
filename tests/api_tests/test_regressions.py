"""
Regression tests for Network objects.
"""

import json
import pytest
import requests

from .fixtures import tornado_server, tornado_app
from .util import (
    assert_error, assert_success, assert_created, assert_deleted, Client,
    load_json, run_set_queries
)


def test_network_bug_issues_34(tornado_server):
    """Test set queries for Networks."""
    client = Client(tornado_server)

    client.create('/sites', name='Test Site')  # 1

    # Pre-load the attributes
    attr_data = load_json('attributes.json')
    client.create(
        '/sites/1/attributes',
        attributes=attr_data['attributes']
    )

    # Populate the device objects.
    network_data = load_json('networks.json')
    client.create(
        '/sites/1/networks',
        networks=network_data['networks']
    )

    # Filter networks w/ attribute hostname=foo-bar1
    n1_output = load_json('networks/bug_issues_34_1.json')
    assert_success(
        client.get("/sites/1/networks?attributes=hostname=foo-bar1"),
        n1_output['data'],
    )

    # Filter networks w/ attribute hostname=foo-bar1, including IPs
    n2_output = load_json('networks/bug_issues_34_2.json')
    assert_success(
        client.get("/sites/1/networks?attributes=hostname=foo-bar1&include_ips=True"),
        n2_output['data'],
    )
