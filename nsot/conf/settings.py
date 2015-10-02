"""
Django settings for nsot project using Django 1.8.
"""


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import macaddress
from netaddr import eui
import os
import re

# Path where the code is found. (aka project root)
BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))

# Path where the config file is found.
CONF_ROOT = os.path.abspath(os.path.dirname(__file__))

# A boolean that turns on/off debug mode. Never deploy a site into production
# with DEBUG turned on.
# Default: False
DEBUG = False

#################
# Core Settings #
#################

# A tuple of strings designating all applications that are enabled in this
# Django installation.
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_filters',
    'polymorphic',
    'smart_selects',
    'rest_framework',
    'rest_framework_swagger',
    'custom_user',
    'nsot',
)

# The model to use to represent a User.
AUTH_USER_MODEL = 'nsot.User'

# A tuple of authentication backend classes (as strings) to use when attempting
# to authenticate a user.
# https://docs.djangoproject.com/en/1.8/topics/auth/customizing/#authentication-backends
AUTHENTICATION_BACKENDS = (
    'nsot.middleware.auth.EmailHeaderBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# A tuple of middleware classes to use.
# https://docs.djangoproject.com/en/1.8/topics/http/middleware/
MIDDLEWARE_CLASSES = (
    'nsot.middleware.request_logging.LoggingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'nsot.middleware.auth.EmailHeaderMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

# A string representing the full Python import path to your root URLconf.
ROOT_URLCONF = 'nsot.conf.urls'

# The full Python path of the WSGI application object that Django's built-in
# servers (e.g. runserver) will use.
WSGI_APPLICATION = 'nsot.wsgi.application'

# When set to True, if the request URL does not match any of the patterns in the
# URLconf and it doesn't end in a slash, an HTTP redirect is issued to the same
# URL with a slash appended. Note that the redirect may cause any data submitted
# in a POST request to be lost.
# Default: True
APPEND_SLASH = True

from nsot.version import __version__
NSOT_VERSION = __version__

# Template loaders. The NSoT web UI is written in Angular.js using Jinja2
# templates.
TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.csrf",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "extensions": [
                "jinja2.ext.do",
                "jinja2.ext.loopcontrols",
                "jinja2.ext.with_",
                "jinja2.ext.i18n",
                "jinja2.ext.autoescape",
                "django_jinja.builtins.extensions.CsrfExtension",
                "django_jinja.builtins.extensions.CacheExtension",
                "django_jinja.builtins.extensions.TimezoneExtension",
                "django_jinja.builtins.extensions.UrlsExtension",
                "django_jinja.builtins.extensions.StaticFilesExtension",
                "django_jinja.builtins.extensions.DjangoFiltersExtension",
            ],
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates').replace('\\','/'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.csrf",
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'nsot.ui.context_processors.app_version',
            ],
        },
    },
]

##################
# REST Framework #
##################

# Settings for Django REST Framework (DRF)
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        # 'rest_framework.renderers.AdminRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'nsot.api.pagination.CustomPagination',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'nsot.api.auth.AuthTokenAuthentication',
        'nsot.api.auth.EmailHeaderAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'EXCEPTION_HANDLER': 'nsot.exc.custom_exception_handler',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'PAGE_SIZE': None,
}

############
# Database #
############
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'nsot.sqlite3'),
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

# The name of the cookie to use for the CSRF authentication token.
# Default: 'csrftoken'
CSRF_COOKIE_NAME = '_xsrf'

# Coming in Django 1.9
# The name of the request header used for CSRF authentication.
# https://github.com/django/django/commit/668d53c
# Default: 'X-CSRFToken'
# CSRF_HEADER_NAME = 'X-XSRFToken'

################
# Static files #
################

# (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

# URL to use when referring to static files located in STATIC_ROOT.
# Default: '/static/'
STATIC_URL = '/static/'

# This setting defines the additional locations the staticfiles app will
# traverse if the FileSystemFinder finder is enabled, e.g. if you use the
# collectstatic or findstatic management command or use the static file serving
# view.
# Default: $BASE_DIR/static
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# The absolute path to the directory where collectstatic will collect static
# files for deployment.
# Default: $BASE_DIR/staticfiles'
STATIC_ROOT = os.path.realpath(os.path.join(BASE_DIR, 'staticfiles'))

###########
# Swagger #
###########

SWAGGER_SETTINGS = {
    'exclude_namespaces': ['.*', 'attribute_types'],
    #'api_version': __version__,
}


###########
# Logging #
###########
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers':['console'],
            'propagate': True,
            'level':'ERROR',
        },
        'nsot': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'rest_framework': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    }
}

##############
# Attributes #
##############

# Acceptable regex pattern for naming Attribute objects.
ATTRIBUTE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")

##############
# Interfaces #
##############

# The default format for displaying MAC addresses. This defaults to
# ":"-separated and expanded (e.g. '00:00:00:00:00:00')
MACADDRESS_DEFAULT_DIALECT = 'macaddress.mac_linux'

# The default speed in Mbps for newly device interfaces if not otherwise
# specified.
INTERFACE_DEFAULT_SPEED = 1000  # In Mbps (e.g. 1Gbps)

# Default MAC address ('00:00:00:00:00:00')
INTERFACE_DEFAULT_MAC = eui.EUI(0, dialect=macaddress.default_dialect())

# These are mappings to the formal integer types from SNMP IF-MIB::ifType. The
# types listed here are the most commonly found in the wild.
#
# *IF YOU ARE GOING TO MODIFY THIS*: This MUST be a list of 2-tuples of (iftype,
# name), where iftype is the unique ID for the IANA ifType SNMP MIB, and name is
# whatever name your little heart desires, but hopefully matches the legit
# description according to the MIB.
#
# Ref: https://www.iana.org/assignments/ianaiftype-mib/ianaiftype-mib
INTERFACE_TYPE_CHOICES = (
    (6, 'ethernet'),       # for all ethernet-like interfaces
    (1, 'other'),          # none of the following
    (135, 'l2vlan'),       # Layer 2 Virtual LAN using 802.1Q
    (136, 'l3vlan'),       # Layer 3 Virtual LAN using IP
    (161, 'lag'),          # IEEE 802.3ad Link Aggregat
    (24, 'loopback'),      # softwareLoopback
    (150, 'mpls'),         # MPLS Tunnel Virtual Interface
    (53, 'prop_virtual'),  # proprietary virtual/internal
    (131, 'tunnel'),       # Encapsulation interface
)

INTERFACE_DEFAULT_TYPE = 6  # ethernet

############
# Networks #
############

# How long is an interconnect? (aka a point-to-point link)
NETWORK_INTERCONNECT_PREFIXLEN = 31

# CIDR prefix lengths for host addresses
HOST_PREFIXES = (32, 128)

# Valid IP versions
IP_VERSIONS = ('4', '6')
