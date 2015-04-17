"""
WSGI config for nsot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nsot.conf.settings")

from django.conf import settings


# If we're set to serve static files ourself (default), wrap the app w/ Cling
# (provided by dj-static).
if settings.SERVE_STATIC_FILES:
    from dj_static import Cling
    application = Cling(get_wsgi_application())
else:
    application = get_wsgi_application()
