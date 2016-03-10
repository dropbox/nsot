"""
This configuration file is just Python code. You may override any global
defaults by specifying them here.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""


from nsot.conf.settings import *
import os.path


# Path where the config is found.
CONF_ROOT = os.path.dirname(__file__)

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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(CONF_ROOT, 'nsot.sqlite3'),
        'USER': 'nsot',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

###############
# Application #
###############

# The address on which the application will listen.
# Default: localhost
NSOT_HOST = 'localhost'

# The port on which the application will be accessed.
# Default: 8990
NSOT_PORT = 8990

# The number of gunicorn worker processes for handling requests.
# Default: 4
NSOT_NUM_WORKERS = 4

# Timeout in seconds before gunicorn workers are killed/restarted.
# Default: 30
NSOT_WORKER_TIMEOUT = 30

# If True, serve static files directly from the app.
# Default: True
SERVE_STATIC_FILES = True

############
# Security #
############

# A URL-safe base64-encoded 32-byte key. This must be kept secret. Anyone with
# this key is able to create and read messages. This key is used for
# encryption/decryption of sessions and auth tokens. A unique key is randomly
# generated for you when you utilize ``nsot-server init``
# https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet.generate_key
SECRET_KEY = u'fMK68NKgazLCjjTXjDtthhoRUS8IV4lwD-9G7iVd2Xs='

# Header to check for Authenticated Email. This is intended for use behind an
# authenticating reverse proxy.
USER_AUTH_HEADER = 'X-NSoT-Email'

# The age, in seconds, until an AuthToken granted by the API will expire.
# Default: 600
AUTH_TOKEN_EXPIRY = 600  # 10 minutes

# A list of strings representing the host/domain names that this Django site can
# serve. This is a security measure to prevent an attacker from poisoning caches
# and triggering password reset emails with links to malicious hosts by
# submitting requests with a fake HTTP Host header, which is possible even under
# many seemingly-safe web server configurations.
# https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

##############
# Interfaces #
##############

# The default format for displaying MAC addresses. This defaults to
# ":"-separated and expanded (e.g. '00:00:00:00:00:00')
MACADDRESS_DEFAULT_DIALECT = 'macaddress.mac_linux'

# The default speed in Mbps for newly device interfaces if not otherwise
# specified.
INTERFACE_DEFAULT_SPEED = 1000  # In Mbps (e.g. 1Gbps)

# Whether to compress IPv6 for display purposes, for example:
# - Default: 2620:0100:6000:0000:0000:0000:0000:0000/40
# - Compressed: 2620:100:6000::/40
# Default: True
NSOT_COMPRESS_IPV6 = True
