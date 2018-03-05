"""
Test NSoT utilities.
"""

from __future__ import unicode_literals, print_function

import pytest

from nsot import models, util


def test_parse_set_query():
    """
    Parse a bunch of set queries and make sure that the expected result
    matches.
    """
    # Dict of tuples of (query: expected_result)
    set_tests = {
        'foo=bar': [
            ('intersection', 'foo', 'bar'),
        ],
        'foo=bar owner=jathan': [
            ('intersection', 'foo', 'bar'),
            ('intersection', 'owner', 'jathan'),
        ],
        '-owner=gary': [
            ('difference', 'owner', 'gary'),
        ],
        'cluster +foo=baz': [
            ('intersection', 'cluster', ''),
            ('union', 'foo', 'baz'),
        ],
        # Extra white space
        'cluster=lax   +foo=baz': [
            ('intersection', 'cluster', 'lax'),
            ('union', 'foo', 'baz'),
        ],
        # Single-quoted value w/ a space in it
        "usage='Internal Network'": [
            ('intersection', 'usage', 'Internal Network'),
        ],
        # Double-quoted value w/ a space in it
        'usage="Internal Network"': [
            ('intersection', 'usage', 'Internal Network'),
        ],
    }

    # Make sure that result matches expected_result
    for query, expected_result in set_tests.iteritems():
        result = util.parse_set_query(query)
        assert result == expected_result

    # Test bogus stuff
    with pytest.raises(TypeError):
        util.parse_set_query(None)

    # Test a bad string
    with pytest.raises(ValueError):
        util.parse_set_query('foo="bar')  # Unbalanced quotes


PARENT = '10.47.216.0/22'
HOSTS = [
    '10.47.216.9/32', '10.47.216.10/32', '10.47.216.11/32', '10.47.216.12/32',
    '10.47.216.13/32', '10.47.216.14/32', '10.47.216.24/32', '10.47.216.25/32',
    '10.47.216.26/32', '10.47.216.27/32', '10.47.216.32/32', '10.47.216.33/32',
    '10.47.216.34/32', '10.47.216.35/32', '10.47.216.40/32', '10.47.216.41/32',
    '10.47.216.58/32', '10.47.216.59/32', '10.47.219.0/32', '10.47.219.1/32',
    '10.47.219.2/32', '10.47.219.3/32', '10.47.219.4/32', '10.47.219.5/32',
    '10.47.219.6/32', '10.47.219.7/32', '10.47.219.8/32', '10.47.219.9/32',
    '10.47.219.10/32', '10.47.219.11/32', '10.47.219.12/32', '10.47.219.13/32',
    '10.47.219.14/32', '10.47.219.15/32', '10.47.219.16/32', '10.47.219.17/32',
    '10.47.219.18/32', '10.47.219.19/32', '10.47.219.20/32', '10.47.219.21/32',
    '10.47.219.22/32', '10.47.219.23/32', '10.47.219.24/32', '10.47.219.25/32',
    '10.47.219.26/32', '10.47.219.27/32', '10.47.219.28/32', '10.47.219.29/32',
    '10.47.219.30/32', '10.47.219.31/32', '10.47.219.32/32', '10.47.219.33/32',
    '10.47.219.34/32', '10.47.219.35/32', '10.47.219.36/32', '10.47.219.37/32',
    '10.47.219.38/32', '10.47.219.39/32', '10.47.219.40/32', '10.47.219.41/32',
    '10.47.219.42/32', '10.47.219.43/32', '10.47.219.44/32', '10.47.219.45/32',
    '10.47.219.46/32', '10.47.219.47/32', '10.47.219.48/32', '10.47.219.49/32',
    '10.47.219.50/32', '10.47.219.51/32', '10.47.219.52/32', '10.47.219.53/32',
    '10.47.219.54/32', '10.47.219.55/32', '10.47.219.56/32', '10.47.219.57/32',
    '10.47.219.58/32', '10.47.219.59/32', '10.47.219.60/32', '10.47.219.61/32',
    '10.47.219.62/32', '10.47.219.63/32', '10.47.219.64/32', '10.47.219.65/32',
    '10.47.219.68/32', '10.47.219.69/32', '10.47.219.72/32', '10.47.219.73/32',
    '10.47.219.78/32', '10.47.219.79/32', '10.47.219.80/32', '10.47.219.81/32',
    '10.47.219.82/32', '10.47.219.83/32', '10.47.219.84/32', '10.47.219.85/32',
    '10.47.219.86/32', '10.47.219.87/32', '10.47.219.88/32', '10.47.219.89/32',
    '10.47.219.90/32', '10.47.219.91/32', '10.47.219.92/32', '10.47.219.93/32',
    '10.47.219.94/32', '10.47.219.95/32', '10.47.219.96/32', '10.47.219.97/32',
    '10.47.219.98/32', '10.47.219.99/32', '10.47.219.100/32',
    '10.47.219.101/32', '10.47.219.102/32', '10.47.219.103/32',
    '10.47.219.104/32', '10.47.219.105/32', '10.47.219.106/32',
    '10.47.219.107/32', '10.47.219.108/32', '10.47.219.109/32',
    '10.47.219.110/32', '10.47.219.111/32', '10.47.219.112/32',
    '10.47.219.113/32', '10.47.219.114/32', '10.47.219.115/32',
    '10.47.219.116/32', '10.47.219.117/32', '10.47.219.118/32',
    '10.47.219.119/32', '10.47.219.120/32', '10.47.219.121/32',
    '10.47.219.122/32', '10.47.219.123/32', '10.47.219.124/32',
    '10.47.219.125/32', '10.47.219.126/32', '10.47.219.127/32',
    '10.47.219.249/32'
]


def test_stats_get_utilization(parent=PARENT, hosts=HOSTS):
    """
    Make sure that getting network utilization stats is accurate.
    """
    expected = '10.47.216.0/22 - 14% used (139), 86% free (885)'
    output = util.calculate_network_utilization(parent, hosts, as_string=True)

    assert output == expected


def test_slugify():
    """Test ``util.slugify()``."""
    cases = [
        ('/', '_'),
        ('my cool string', 'my cool string'),
        ('Ethernet1/2', 'Ethernet1_2'),
        (
            'foo-bar1:xe-0/0/0.0_foo-bar2:xe-0/0/0.0',
            'foo-bar1:xe-0_0_0.0_foo-bar2:xe-0_0_0.0'
        ),
    ]

    for case, expected in cases:
        assert util.slugify(case) == expected


def test_slugify_interface():
    """Test ``util.slugify_interface``."""

    # Test interface dict input
    interface = {'device_hostname': 'foo-bar1', 'name': 'ge-0/0/1'}
    expected = 'foo-bar1:ge-0/0/1'
    assert util.slugify_interface(interface) == expected

    # Test kwarg input
    assert util.slugify_interface(**interface) == expected

    # Test bad inputs
    with pytest.raises(RuntimeError):
        util.slugify_interface()

    with pytest.raises(RuntimeError):
        util.slugify_interface(device_hostname='bogus')

    with pytest.raises(RuntimeError):
        util.slugify_interface(name='bogus')


def test_get_field_attr():
    """Test ``util.get_field_attr()``."""
    model = models.Interface
    field_name = 'parent'
    attr_name = 'help_text'

    # Test desired behavior
    expected = models.Interface._meta.get_field('parent').help_text
    assert util.get_field_attr(model, field_name, attr_name) == expected

    # All bad inputs returns ''
    assert util.get_field_attr(model, field_name, 'bogus') == ''
    assert util.get_field_attr(model, 'bogus', attr_name) == ''
    assert util.get_field_attr(model, 'bogus', 'bogus') == ''
    assert util.get_field_attr('bogus', 'bogus', 'bogus') == ''
