"""
Project-wide utilities.
"""

import collections
import logging
import shlex

from cryptography.fernet import Fernet
from django.core.exceptions import FieldDoesNotExist
from logan.runner import run_app


log = logging.getLogger(__name__)

_TRUTHY = set([
    'true', 'yes', 'on', '1', ''
])


__all__ = (
    'qpbool', 'normalize_auth_header', 'generate_secret_key', 'get_field_attr',
    'SetQuery', 'parse_set_query', 'generate_settings', 'initialize_app',
    'main', 'cidr_to_dict'
)


def qpbool(arg):
    """
    Convert "truthy" strings into Booleans.

    >>> qpbool('true')
    True

    :param arg:
        Truthy string
    """
    return str(arg).lower() in _TRUTHY


def normalize_auth_header(header):
    """
    Normalize a header name into WSGI-compatible format.

    >>> normalize_auth_header('X-NSoT-Email')
    'HTTP_X_NSOT_EMAIL'

    :param header:
        Header name
    """
    return 'HTTP_' + header.upper().replace('-', '_')


def generate_secret_key():
    """
    Return a secret key suitable for use w/ Fernet.

    >>> generate_secret_key()
    '1BpuqeM5d5pi-U2vIsqeQ8YnTrXRRUAfqV-hu6eQ5Gw='
    """
    return Fernet.generate_key()


def get_field_attr(model, field_name, attr):
    """Return the specified field for a model field"""
    try:
        field_data = model._meta.get_field_by_name(field_name)
    except FieldDoesNotExist:
        return ''
    else:
        field, model, direct, m2m = field_data
        return getattr(field, attr, '')


def cidr_to_dict(cidr):
    """
    Take a cidr and return it as a dictionary.

    >>> cidr_to_dict('192.168.0.0/16')
    {'network_address': '192.168.0.0', 'prefix_length': 16}

    :param cidr:
        IPv4/IPv6 CIDR string
    """
    from .. import validators
    cidr = validators.validate_cidr(cidr)
    return {
        'network_address': cidr.network_address,
        'prefix_length': cidr.prefixlen,
    }


#: Namedtuple for resultant items from ``parse_set_query()``
SetQuery = collections.namedtuple('SetQuery', 'action name value')


def parse_set_query(query):
    """
    Parse a representation of set operations for attribute/value pairs into
    (action, name, value) and return a list of ``SetQuery`` objects.

    Computes left-to-right evaluation, where the first character indicates the
    set operation:

    + "+" indicates a union
    + "-" indicates a difference
    + no marker indicates an intersection

    For example::

        >>> parse_set_query('+owner=team-networking')
        [SetQuery(action='union', name='owner', value='team-networking')]
        >>> parse_set_query('foo=bar')
        [SetQuery(action='intersection', name='foo', value='bar')]
        >>> parse_set_query('foo=bar -owner=team-networking')
        [SetQuery(action='intersection', name='foo', value='bar'),
         SetQuery(action='difference', name='owner', value='team-networking')]

    :param query:
        Set query string
    """
    log.debug('Incoming query = %r' % (query,))

    if not isinstance(query, basestring):
        raise TypeError('Query must be a string.')

    queries = shlex.split(query)

    attributes = []
    for q in queries:
        if q.startswith('+'):
            action = 'union'
            q = q[1:]
        elif q.startswith('-'):
            action = 'difference'
            q = q[1:]
        else:
            action = 'intersection'

        name, _, value = q.partition('=')
        attributes.append(SetQuery(action, name, value))

    log.debug('Outgoing attributes = %r' % (attributes,))
    return attributes


#: Configuration template emitted when a user runs ``nsot-server init``.
CONFIG_TEMPLATE = '''
"""
This configuration file is just Python code. You may override any global
defaults by specifying them here.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
from nsot.conf.settings import *

import os.path

# Path where the config is found.
CONF_ROOT = os.path.dirname(__file__)

# A boolean that turns on/off debug mode. Never deploy a site into production
# with DEBUG turned on.
# Default: False
DEBUG = False

############
# Database #
############
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(CONF_ROOT, 'nsot.sqlite3'),
        'USER': 'nsot',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

###############
# Application #
###############

# The address on which the application will listen.
# Default: localhost
NSOT_HOST = 'localhost'

# The port on which the application will be accessed.
# Default: 8990
NSOT_PORT = 8990

# The number of gunicorn worker processes for handling requests.
# Default: 4
NSOT_NUM_WORKERS = 4

# Timeout in seconds before gunicorn workers are killed/restarted.
# Default: 30
NSOT_WORKER_TIMEOUT = 30

# If True, serve static files directly from the app.
# Default: True
SERVE_STATIC_FILES = True

############
# Security #
############

# A URL-safe base64-encoded 32-byte key. This must be kept secret. Anyone with
# this key is able to create and read messages. This key is used for
# encryption/decryption of sessions and auth tokens.
SECRET_KEY = %(secret_key)r

# Header to check for Authenticated Email. This is intended for use behind an
# authenticating reverse proxy.
USER_AUTH_HEADER = 'X-NSoT-Email'

# The age, in seconds, until an AuthToken granted by the API will expire.
# Default: 600
AUTH_TOKEN_EXPIRY = 600  # 10 minutes

# A list of strings representing the host/domain names that this Django site
# can serve. This is a security measure to prevent an attacker from poisoning
# caches and triggering password reset emails with links to malicious hosts by
# submitting requests with a fake HTTP Host header, which is possible even
# under many seemingly-safe web server configurations.
# https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']
'''


def generate_settings(config_template=None):
    """
    Used to emit a generated configuration from ``config_template``.

    :param config_template:
        Config template
    """
    if config_template is None:
        config_template = CONFIG_TEMPLATE.strip()

    secret_key = generate_secret_key()
    return config_template % dict(secret_key=secret_key)


def initialize_app(config):
    """
    Actions to be performed prior to creating the Application object.

    :param config:
        Config object
    """
    USE_GEVENT = True  # Hard-coding gevent for now.

    if USE_GEVENT:
        # TODO(jathan): We need to keep an eye on this. If we run into any race
        # conditions w/ database updates, this should be the first place we
        # look.
        from django.db import connections
        connections['default'].allow_thread_sharing = True


def main():
    """CLI application used to manage NSoT."""
    run_app(
        project='nsot',
        default_config_path='~/.nsot/nsot.conf.py',
        default_settings='nsot.conf.settings',
        settings_initializer=generate_settings,
        settings_envvar='NSOT_CONF',
        initializer=initialize_app,
    )


if __name__ == '__main__':
    main()
