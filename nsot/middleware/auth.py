"""
Middleware for authentication.
"""

import logging

from django.contrib.auth import backends, middleware
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from guardian.backends import ObjectPermissionBackend
from guardian.core import ObjectPermissionChecker

from ..util import normalize_auth_header


log = logging.getLogger('nsot_server')


class EmailHeaderMiddleware(middleware.RemoteUserMiddleware):
    header = normalize_auth_header(settings.USER_AUTH_HEADER)


class EmailHeaderBackend(backends.RemoteUserBackend):
    """Custom backend that validates username is an email."""
    def authenticate(self, request, remote_user):
        """Override default to return None if username is invalid."""
        if not remote_user:
            return

        username = self.clean_username(remote_user)
        if not username:
            return

        return super(EmailHeaderBackend, self).authenticate(
            request, remote_user
        )

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
        """Check whether to make new users superusers."""
        if settings.NSOT_NEW_USERS_AS_SUPERUSER:
            user.is_superuser = True
            user.is_staff = True
            user.save()

        log.debug('Created new user: %s', user)
        return user


class NsotObjectPermissionsBackend(ObjectPermissionBackend):
    """Custom backend that overloads django-guardian's has_perm method."""
    def has_perm(self, user_obj, perm, obj=None):
        """
        Returns ``True`` if ``user_obj`` has ``perm`` for ``obj``. If no
        ``obj`` is provided, ``False`` is returned.

        However, if ``grp_obj`` does not have ``perm`` for ``obj``,
        the ancestor tree for ``obj`` is checked against. If any node in
        the ancestor tree has ``perm`` for the ``obj``, then ``True`` is
        returned, else ``False`` is returned.
        """
        check = super(NsotObjectPermissionsBackend, self).has_perm(
            user_obj, perm, obj
        )
        if check:
            return True

        if hasattr(obj, 'get_ancestors'):
            ancestors = obj.get_ancestors()
            ancestor_perm_check = ObjectPermissionChecker(user_obj)

            return any(ancestor_perm_check.has_perm(perm, a)
                       for a in ancestors)

        return False
