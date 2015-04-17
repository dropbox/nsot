from __future__ import absolute_import, print_function

import sys

import BaseHTTPServer
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
import logging
from optparse import make_option


class Command(BaseCommand):
    args = '<username>'
    help = 'Start a development reverse proxy.'

    option_list = BaseCommand.option_list + (
        make_option('--address', '-a',
            dest='address',
            type=str,
            default='localhost',
            help='Address to listen on',
        ),
        make_option('--listen-port', '-p',
            dest='listen_port',
            type=int,
            default=8888,
            help='Port to listen on.'
        ),
        make_option('--backend-port', '-P',
            dest='backend_port',
            type=int,
            default=8990,
            help='Port to proxy to',
        ),
    )

    def handle(self, username, **options):
        try:
            from mrproxy import UserProxyHandler
        except ImportError:
            raise SystemExit(
                'mrproxy is required for the user proxy. Please see README.md.'
            )

        class ServerArgs(object):
            def __init__(self, backend_port, username):
                self.backend_port = backend_port
                self.header = ['X-NSoT-Email: %s' % username]

        if username is None:
            username = getpass.getuser()
            logging.debug('No username provided, using (%s)', username)
        username += '@localhost'


        address = options.get('address')
        listen_port = options.get('listen_port')

        server = BaseHTTPServer.HTTPServer(
            (address, listen_port), UserProxyHandler
        )
        server.args = ServerArgs(options.get('backend_port'), username)
        try:
            logging.info(
                'Starting user_proxy on %s:%s with user %r',
                address, listen_port, username
            )
            server.serve_forever()
        except KeyboardInterrupt:
            print('Bye!')
