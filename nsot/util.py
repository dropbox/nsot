"""
Project-wide utilities.
"""

import collections
import logging
import tornado
from jinja2 import Environment, PackageLoader

from .settings import settings
from .version import __version__


log = logging.getLogger(__name__)

_TRUTHY = set([
    "true", "yes", "on", "1", ""
])


def qp_to_bool(arg):
    return str(arg).lower() in _TRUTHY


def get_loglevel(args):
    verbose = args.verbose * 10
    quiet = args.quiet * 10
    return logging.getLogger().level - verbose + quiet


def get_template_env(package="nsot", extra_filters=None, extra_globals=None):
    filters = {}
    j_globals = {
        "NSOT_VERSION": __version__,
    }

    if extra_filters:
        filters.update(extra_filters)

    if extra_globals:
        j_globals.update(extra_globals)

    env = Environment(
        loader=PackageLoader(package, "templates"),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True

    )
    env.filters.update(filters)
    env.globals.update(j_globals)

    return env


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
    queries = query.split()

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
