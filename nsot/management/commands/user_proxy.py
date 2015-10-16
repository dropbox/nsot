from __future__ import absolute_import, print_function

"""
Command for starting up an authenticating reverse proxy for use in development.

Please, don't use me in production!
"""


import BaseHTTPServer
from django.conf import settings
import getpass
import socket

from nsot.util.commands import NsotCommand, CommandError


class Command(NsotCommand):
    help = 'Start an authenticating reverse proxy for use in development.'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='?',
            default=getpass.getuser(),
            help='Username used for authentication.',
        )
        parser.add_argument(
            '-a', '--address',
            type=str,
            default=settings.NSOT_HOST,
            help='Address to listen on.',
        )
        parser.add_argument(
            '-d', '--domain',
            type=str,
            default='localhost',
            help='Domain for user account.',
        )
        parser.add_argument(
            '-H', '--auth-header',
            type=str,
            default=settings.USER_AUTH_HEADER,
            help='HTTP user auth header name.',
        )
        parser.add_argument(
            '-P', '--backend-port',
            type=int,
            default=settings.NSOT_PORT,
            help='Port to proxy to.',
        )
        parser.add_argument(
            '-p', '--listen-port',
            type=int,
            default=settings.NSOT_PORT + 1,
            help='Port to listen on.',
        )

    def handle(self, **options):
        username = options.get('username')

        try:
            from mrproxy import UserProxyHandler
        except ImportError:
            raise SystemExit(
                'mrproxy is required for the user proxy. Please see '
                'README.rst.'
            )

        class ServerArgs(object):
            """Argument container for http service."""
            def __init__(self, backend_port, username, auth_header):
                self.backend_port = backend_port
                self.header = ['%s: %s' % (auth_header, username)]

        username = '%s@%s' % (username, options.get('domain'))
        address = options.get('address')
        auth_header = options.get('auth_header')
        backend_port = options.get('backend_port')
        listen_port = options.get('listen_port')

        # Try to start the server
        try:
            server = BaseHTTPServer.HTTPServer(
                (address, listen_port), UserProxyHandler
            )
        except socket.error as err:
            raise CommandError(err)
        else:
            server.args = ServerArgs(backend_port, username, auth_header)

        # Run until we hit ctrl-C
        try:
            print(
                "Starting proxy on %s %s => %s, auth '%s: %s'" %
                (address, backend_port, listen_port, auth_header, username)
            )
            server.serve_forever()
        except KeyboardInterrupt:
            print('Bye!')
