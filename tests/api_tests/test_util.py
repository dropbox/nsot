"""
Test NSoT utilities.
"""

from nsot.util import SetQuery, parse_set_query


def test_parse_set_query():
    """
    Parse a bunch of set queries and make sure that the expected result
    matches.
    """
    # List of 2-tuples of (query, expected_result)
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
    }

    # Make sure that result matches expected_result
    for query, expected_result in set_tests.iteritems():
        result = parse_set_query(query)
        assert result == expected_result
