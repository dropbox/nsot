"""
This configuration file is just Python code. You may override any global
defaults by specifying them here.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
from nsot.conf.settings import *  # noqa

import os

# Path where the config is found.
CONF_ROOT = '/etc/nsot'

# A boolean that turns on/off debug mode. Never deploy a site into production
# with DEBUG turned on.
# Default: False
DEBUG = False

############
# Database #
############
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', 'nsot.sqlite3'),
        'USER': os.environ.get('DB_USER', 'nsot'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', '')
    }
}

###############
# Application #
###############

# The address on which the application will listen.
# Default: localhost
NSOT_HOST = '0.0.0.0'

# The port on which the application will be accessed.
# Default: 8990
NSOT_PORT = 8990

# If True, serve static files directly from the app.
# Default: True
SERVE_STATIC_FILES = True

############
# Security #
############

# A URL-safe base64-encoded 32-byte key. This must be kept secret. Anyone with
# this key is able to create and read messages. This key is used for
# encryption/decryption of sessions and auth tokens.
SECRET_KEY = os.environ.get(
    'NSOT_SECRET', 'nJvyRB8tckUWvquJZ3ax4QnhpmqTgVX2k3CDY13yK9E='
)

# Header to check for Authenticated Email. This is intended for use behind an
# authenticating reverse proxy.
USER_AUTH_HEADER = os.environ.get('NSOT_EMAIL', 'X-NSoT-Email')

# The age, in seconds, until an AuthToken granted by the API will expire.
# Default: 600
AUTH_TOKEN_EXPIRY = 600  # 10 minutes

# A list of strings representing the host/domain names that this Django site
# can serve. This is a security measure to prevent an attacker from poisoning
# caches and triggering password reset emails with links to malicious hosts by
# submitting requests with a fake HTTP Host header, which is possible even
# under many seemingly-safe web server configurations.
# https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']
