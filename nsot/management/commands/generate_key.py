from __future__ import absolute_import, print_function

"""Command to generate a secret key."""

from cryptography.fernet import Fernet

from nsot.util.commands import NsotCommand


class Command(NsotCommand):
    help = (
        'Generate a URL-safe base64-encoded 32-byte key for use in '
        'settings.SECRET_KEY.'
    )

    def handle(self, **options):
        print(Fernet.generate_key())
