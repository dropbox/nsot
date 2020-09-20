from __future__ import absolute_import
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import logging
from rest_framework import authentication
from rest_framework import exceptions


from ..util import normalize_auth_header


log = logging.getLogger(__name__)


class AuthTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        log.debug("Fetching AuthToken header.")

        auth_header = authentication.get_authorization_header(request)
        auth_fields = auth_header.decode("utf-8").split()

        if not auth_fields or auth_fields[0].lower() != "authtoken":
            return None

        if len(auth_fields) == 1:
            raise exceptions.AuthenticationFailed(
                "Invalid token header. No credentials provided."
            )
        elif len(auth_fields) > 2:
            raise exceptions.AuthenticationFailed(
                "Invalid token header. Token should not contain spaces."
            )

        auth_type, data = auth_fields
        email, auth_token = data.split(":", 1)

        log.debug("     email: %r", email)
        log.debug("auth_token: %r", auth_token)

        return self.authenticate_credentials(email, auth_token)

    def authenticate_credentials(self, email, auth_token):
        user = get_user_model().verify_auth_token(email, auth_token)

        # If user is bad this time, it's an invalid login
        if user is None:
            raise exceptions.AuthenticationFailed(
                "Invalid login/token expired."
            )
            # raise exc.Unauthorized('Invalid login/token expired.')

        log.debug("token_auth authenticated user: %s" % email)

        return (user, auth_token)

    def authenticate_header(self, request):
        return "AuthToken"


class EmailHeaderAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        user_auth_header = normalize_auth_header(settings.USER_AUTH_HEADER)
        log.debug(
            "EmailHeaderAuthentication.authenticate(): auth_header = %r",
            user_auth_header,
        )

        # Naively fetch the user email from the auth_header
        email = request.META.get(user_auth_header)
        log.debug(
            "EmailHeaderAuthentication.authenticate(): email = %r", email
        )
        if email is None:
            return None

        # Fetch a stinkin' user
        try:
            user = get_user_model().objects.get(email=email)
        except ObjectDoesNotExist:
            # Make this a 400 for now since it's failing validation.
            raise exceptions.ValidationError(
                "Username must contain a valid email address"
            )

        # And return it.
        return (user, None)


class SecretKeyAuthentication(authentication.BaseAuthentication):
    def authenticate_credentials(self, email, secret_key):
        try:
            user = get_user_model().objects.get(email=email)
        except ObjectDoesNotExist:
            user = None

        # Make sure we've got a user and the secret_key is valid
        if user is not None and user.verify_secret_key(secret_key):
            return user, secret_key  # Auth success

        raise exceptions.AuthenticationFailed("Invalid email/secret_key")
