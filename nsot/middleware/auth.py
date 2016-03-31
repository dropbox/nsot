"""
Middleware for authentication.
"""

from django.contrib.auth import backends, middleware
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.log import getLogger

from ..util import normalize_auth_header


log = getLogger('nsot_server')


class EmailHeaderMiddleware(middleware.RemoteUserMiddleware):
    header = normalize_auth_header(settings.USER_AUTH_HEADER)


class EmailHeaderBackend(backends.RemoteUserBackend):
    """Custom backend that validates username is an email."""
    def authenticate(self, remote_user):
        """Override default to return None if username is invalid."""
        if not remote_user:
            return
        username = self.clean_username(remote_user)
        if not username:
            return

        return super(EmailHeaderBackend, self).authenticate(remote_user)

    def clean_username(self, username):
        """Makes sure that the username is a valid email address."""
        validator = EmailValidator()
        try:
            validator(username)  # If invalid, will raise a ValidationError
        except ValidationError:
            log.debug('Invalid email address: %r', username)
            return None
        else:
            return username

    def configure_user(self, user):
        """Make all new users superusers and staff."""
        user.is_superuser = True
        user.is_staff = True
        user.save()
        log.debug('Created new user: %s', user)
        return user
