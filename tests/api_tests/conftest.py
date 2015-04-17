"""
Configuration file for the unit tests via py.test.
"""

import betamax
import os


CASSETTE_DIR = 'tests/api_tests/cassettes'


# Tell Betamax where to save the cassette fixtures.
with betamax.Betamax.configure() as config:

    if not os.path.exists(CASSETTE_DIR):
        os.makedirs(CASSETTE_DIR)

    config.cassette_library_dir = 'tests/api_tests/cassettes'
    config.default_cassette_options['record_mode'] = 'all'
