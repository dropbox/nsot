"""
NSoT demo settings.
"""
from nsot.conf.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'demo.sqlite3',
    }
}

SECRET_KEY = u'fMK68NKgazLCjjTXjDtthhoRUS8IV4lwD-9G7iVd2Xs='

AUTH_TOKEN_EXPIRY = 60 * 60 * 3  # 30 minutes

STATIC_ROOT = 'staticfiles'

# The address on which the application will listen.
# Default: localhost
NSOT_HOST = '0.0.0.0'

# The port on which the application will be accessed.
# Default: 8990
NSOT_PORT = 8990
