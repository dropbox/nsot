from __future__ import absolute_import, print_function

import sys

from cryptography.fernet import Fernet
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Generate a URL-safe base64-encoded 32-byte key for use in '
        'settings.SECRET_KEY.'
    )

    def handle(self, **options):
        print(Fernet.generate_key())
