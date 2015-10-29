from __future__ import absolute_import, print_function

"""
Command to start the NSoT server process.
"""

from django.conf import settings
from django.core.management import call_command
import sys

from nsot.services import http
from nsot.util.commands import NsotCommand, CommandError


class Command(NsotCommand):
    help = 'Start the NSoT server process.'

    def add_arguments(self, parser):
        parser.add_argument(
            'service',
            nargs='?',
            default='http',
            help='Starts the specified service.',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            default=False,
            help='Toggle debug output.',
        )
        parser.add_argument(
            '--max-requests',
            type=int,
            default=settings.NSOT_MAX_REQUESTS,
            help=(
                'The maximum number of requests a worker will process before '
                'restarting.'
            ),
        )
        parser.add_argument(
            '--max-requests-jitter',
            type=int,
            default=settings.NSOT_MAX_REQUESTS_JITTER,
            help=(
                'The maximum jitter to add to the max_requests setting.'
            ),
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            default=False,
            help='Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '--no-collectstatic',
            action='store_false',
            dest='collectstatic',
            default=True,
            help='Do not automatically collect static files into STATIC_ROOT.',
        )
        parser.add_argument(
            '--no-upgrade',
            action='store_false',
            dest='upgrade',
            default=True,
            help='Do not automatically perform any database upgrades.',
        )
        parser.add_argument(
            '--preload',
            action='store_true',
            default=settings.NSOT_PRELOAD,
            help=(
                'Load application code before the worker processes are '
                'forked.'
            ),
        )
        parser.add_argument(
            '-a', '--address',
            type=str,
            default='%s:%s' % (settings.NSOT_HOST, settings.NSOT_PORT),
            help='Host:port to listen on.',
        )
        parser.add_argument(
            '-k', '--worker-class',
            type=str,
            default=settings.NSOT_WORKER_CLASS,
            help='The type of gunicorn workers to use.',
        )
        parser.add_argument(
            '-t', '--timeout',
            type=int,
            default=settings.NSOT_WORKER_TIMEOUT,
            help='Timeout before gunicorn workers are killed/restarted.',
        )
        parser.add_argument(
            '-w', '--workers',
            type=int,
            default=settings.NSOT_NUM_WORKERS,
            help=(
                'The number of gunicorn worker processes for handling '
                'requests.'
            ),
        )

    def handle(self, **options):
        address = options.get('address')

        # Break address into host:port
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

        # Ensure we perform an upgrade before starting any service.
        if options.get('upgrade'):
            print("Performing upgrade before service startup...")
            call_command(
                'upgrade', verbosity=0, noinput=options.get('noinput')
            )

        # Ensure we collect static before starting any service, but only if
        # SERVE_STATIC_FILES=True.
        if options.get('collectstatic') and settings.SERVE_STATIC_FILES:
            print("Performing collectstatic before service startup...")
            call_command('collectstatic', interactive=False, ignore=['src'])

        service_name = options.get('service')
        try:
            service_class = services[service_name]
        except KeyError:
            raise CommandError('%r is not a valid service' % service_name)

        service = service_class(
            debug=options.get('debug'),
            host=host,
            port=port,
            workers=options.get('workers'),
            worker_class=options.get('worker_class'),
            timeout=options.get('timeout'),
            max_requests=options.get('max_requests'),
            max_requests_jitter=options.get('max_requests_jitter'),
            preload=options.get('preload'),
        )

        # Remove command line arguments to avoid optparse failures with service
        # code that calls call_command which reparses the command line, and if
        # --no-upgrade is supplied a parse error is thrown.
        sys.argv = sys.argv[:1]

        service.run()
