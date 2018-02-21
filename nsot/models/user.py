from __future__ import unicode_literals

import json
import logging

from cryptography.fernet import (Fernet, InvalidToken)
from custom_user.models import AbstractEmailUser
from django.conf import settings
from django.db import models

from .. import exc, util, validators
from .site import Site


log = logging.getLogger(__name__)


class User(AbstractEmailUser):
    """A custom user object that utilizes email as the username."""
    secret_key = models.CharField(
        max_length=44, default=util.generate_secret_key,
        help_text="The user's secret_key used for API authentication."
    )

    @property
    def username(self):
        return self.get_username()

    def get_permissions(self):
        permissions = []
        if self.is_staff or self.is_superuser:
            permissions.append('admin')
        sites = Site.objects.all()

        return {
            str(site.id): {
                'permissions': permissions,
                'site_id': site.id,
                'user_id': self.id
            }
            for site in sites
        }

    def rotate_secret_key(self):
        self.secret_key = util.generate_secret_key()
        self.save()

    def generate_auth_token(self):
        """Serialize user data and encrypt token."""
        # Serialize data
        data = json.dumps({'email': self.email})

        # Encrypt w/ servers's secret_key
        f = Fernet(bytes(settings.SECRET_KEY))
        auth_token = f.encrypt(bytes(data))
        return auth_token

    def verify_secret_key(self, secret_key):
        """Validate secret_key"""
        return secret_key == self.secret_key

    @classmethod
    def verify_auth_token(cls, email, auth_token, expiration=None):
        """Verify token and return a User object."""
        if expiration is None:
            expiration = settings.AUTH_TOKEN_EXPIRY

        # First we lookup the user by email
        query = cls.objects.filter(email=email)
        user = query.first()

        if user is None:
            log.debug('Invalid user when verifying token')
            raise exc.ValidationError({
                'auth_token': 'Invalid user when verifying token'
            })
            # return None  # Invalid user

        # Decrypt auth_token w/ user's secret_key
        f = Fernet(bytes(settings.SECRET_KEY))
        try:
            decrypted_data = f.decrypt(bytes(auth_token), ttl=expiration)
        except InvalidToken:
            log.debug('Invalid/expired auth_token when decrypting.')
            raise exc.ValidationError({
                'auth_token': 'Invalid/expired auth_token.'
            })
            # return None  # Invalid token

        # Deserialize data
        try:
            data = json.loads(decrypted_data)
        except ValueError:
            log.debug('Token could not be deserialized.')
            raise exc.ValidationError({
                'auth_token': 'Token could not be deserialized.'
            })
            # return None  # Valid token, but expired

        if email != data['email']:
            log.debug('Invalid user when deserializing.')
            raise exc.ValidationError({
                'auth_token': 'Invalid user when deserializing.'
            })
            # return None  # User email did not match payload
        return user

    def clean_email(self, value):
        return validators.validate_email(value)

    def clean_fields(self, exclude=None):
        self.email = self.clean_email(self.email)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(User, self).save(*args, **kwargs)

    def to_dict(self, with_permissions=False, with_secret_key=False):
        out = [
            ('id', self.id),
            ('email', self.email),
        ]

        if with_secret_key:
            out.append(('secret_key', self.secret_key))

        if with_permissions:
            out.append(('permissions', self.get_permissions()))

        return dict(out)
