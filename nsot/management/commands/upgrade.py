from __future__ import absolute_import, print_function

"""
Command for running any pending upgrades.
"""

from django.core.management import call_command

from nsot.util.commands import NsotCommand


class Command(NsotCommand):
    help = 'Performs any pending database migrations and upgrades'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput',
            action='store_true',
            default=False,
            help='Tells Django to NOT prompt the user for input of any kind.',
        )

    def handle(self, **options):
        call_command(
            'migrate',
            interactive=(not options['noinput']),
            traceback=options['traceback'],
            verbosity=options['verbosity'],
        )
