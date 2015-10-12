from __future__ import absolute_import, print_function

"""
Command for starting up an authenticating reverse proxy for use in development.

Please, don't use me in production!
"""


import BaseHTTPServer
from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError
import getpass
import logging
from optparse import make_option


log = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '<username>'
    help = 'Start a development reverse proxy.'

    option_list = BaseCommand.option_list + (
        make_option(
            '--address', '-a',
            dest='address',
            type=str,
            default=settings.NSOT_HOST,
            help='Address to listen on. (default: %s)' % settings.NSOT_HOST,
        ),
        make_option(
            '--auth-header', '-H',
            dest='auth_header',
            type=str,
            default=settings.USER_AUTH_HEADER,
            help=(
                'HTTP user auth header name. (default: %s)' %
                settings.USER_AUTH_HEADER
            )
        ),
        make_option(
            '--listen-port', '-p',
            dest='listen_port',
            type=int,
            default=settings.NSOT_PORT + 1,
            help='Port to listen on. (default: %s)' % (settings.NSOT_PORT + 1)
        ),
        make_option(
            '--backend-port', '-P',
            dest='backend_port',
            type=int,
            default=settings.NSOT_PORT,
            help='Port to proxy to. (default: %s)' % settings.NSOT_PORT
        ),
    )

    def handle(self, username, **options):
        try:
            from mrproxy import UserProxyHandler
        except ImportError:
            raise SystemExit(
                'mrproxy is required for the user proxy. Please see '
                'README.rst.'
            )

        class ServerArgs(object):
            def __init__(self, backend_port, username, auth_header):
                self.backend_port = backend_port
                self.header = ['%s: %s' % (auth_header, username)]

        if username is None:
            username = getpass.getuser()
            logging.debug('No username provided, using (%s)', username)

        username += '@localhost'
        address = options.get('address')
        auth_header = options.get('auth_header')
        backend_port = options.get('backend_port')
        listen_port = options.get('listen_port')

        server = BaseHTTPServer.HTTPServer(
            (address, listen_port), UserProxyHandler
        )
        server.args = ServerArgs(backend_port, username, auth_header)
        try:
            logging.info(
                "Starting user_proxy on %s:%s with auth '%s: %s'",
                address, listen_port, username
            )
            server.serve_forever()
        except KeyboardInterrupt:
            print('Bye!')
