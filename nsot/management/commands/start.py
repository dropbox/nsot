from __future__ import absolute_import, print_function

import sys

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
import logging
from optparse import make_option


class Command(BaseCommand):
    args = '<service>'
    help = 'Starts the specified service'

    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            help='Toggle debug output.',
            default=False),
        make_option('--no-upgrade',
            action='store_false',
            dest='upgrade',
            help='Do not automatically perform any database upgrades.',
            default=True),
        make_option('--no-collectstatic',
            action='store_false',
            dest='collectstatic',
            help='Do not automatically collect static files into STATIC_ROOT.',
            default=True),
        make_option('--workers', '-w',
            dest='workers',
            type=int,
            help='The number of gunicorn worker processes for handling requests.',
            default=None),
        make_option('--worker-class', '-k',
            dest='worker_class',
            type=str,
            help='The type of gunicorn workers to use.',
            default=None),
        make_option('--noinput',
            action='store_true',
            dest='noinput',
            default=False,
            help='Tells Django to NOT prompt the user for input of any kind.',
        ),
    )

    def handle(self, service_name='http', address=None, upgrade=True,
               collectstatic=True, **options):
        from nsot.services import http

        if address:
            if ':' in address:
                host, port = address.split(':', 1)
                port = int(port)
            else:
                host = address
                port = None
        else:
            host, port = None, None

        services = {
            'http': http.NsotHTTPServer,
        }

        if upgrade:
            # Ensure we perform an upgrade before starting any service
            print("Performing upgrade before service startup...")
            call_command('upgrade', verbosity=0, noinput=options.get('noinput'))

        if collectstatic and settings.SERVE_STATIC_FILES:
            # Ensure we collect static before starting any service, but only if
            # SERVE_STATIC_FILES=True.
            print("Performing collectstatic before service startup...")
            call_command('collectstatic', interactive=False, ignore=['src'])

        try:
            service_class = services[service_name]
        except KeyError:
            raise CommandError('%r is not a valid service' % service_name)

        service = service_class(
            debug=options.get('debug'),
            host=host,
            port=port,
            workers=options.get('workers'),
            worker_class=options.get('worker_class')
        )

        # Remove command line arguments to avoid optparse failures with service
        # code that calls call_command which reparses the command line, and if
        # --no-upgrade is supplied a parse error is thrown.
        sys.argv = sys.argv[:1]

        print('Running service: %r' % service_name)
        service.run()
