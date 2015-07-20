from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

from ..api.views import NotFoundViewSet
from ..ui.views import FeView


# Custom error-handling views.
handler400 = 'nsot.ui.views.handle400'
handler403 = 'nsot.ui.views.handle403'
handler404 = 'nsot.ui.views.handle404'
handler500 = 'nsot.ui.views.handle500'


urlpatterns = [
    # API
    url(r'^api/', include('nsot.api.urls')),

    # Catchall for missing endpoints
    url(r'^api/.*/$', NotFoundViewSet.as_view({'get': 'list'})),

    # Docs (Swagger)
    url(r'^docs/', include('rest_framework_swagger.urls')),

    # Admin
    url(r'^admin/', include(admin.site.urls)),

    # Favicon redirect for when people insist on fetching it from /favicon.ico
    url(r'^favicon\.ico$',
        RedirectView.as_view(url='%sbuild/images/favicon/favicon.ico' %
        settings.STATIC_URL, permanent=True), name='favicon'),

    # FE handlers
    # Catch index
    url(r'^$', FeView.as_view(), name='index'),

    # Catch all for remaining URLs
    url(r'^.*/$', FeView.as_view(), name='index'),
]
