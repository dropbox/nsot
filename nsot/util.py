import logging
import tornado
from jinja2 import Environment, PackageLoader

from .settings import settings

_TRUTHY = set([
    "true", "yes", "1", ""
])


def qp_to_bool(arg):
    return str(arg).lower() in _TRUTHY


def get_loglevel(args):
    verbose = args.verbose * 10
    quiet = args.quiet * 10
    return logging.getLogger().level - verbose + quiet


def get_template_env(package="nsot", extra_filters=None, extra_globals=None):
    filters = {}
    j_globals = {}

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
