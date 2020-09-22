from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from django.views.generic import RedirectView
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer

from ..api.views import NotFoundViewSet
from ..ui.views import FeView


# Custom error-handling views.
handler400 = "nsot.ui.views.handle400"
handler403 = "nsot.ui.views.handle403"
handler404 = "nsot.ui.views.handle404"
handler500 = "nsot.ui.views.handle500"

# This is the basic API explorer for Swagger/OpenAPI 2.0
schema_view = get_schema_view(
    title="NSoT API",
    renderer_classes=[JSONOpenAPIRenderer],
)

urlpatterns = [
    # API
    path("api/", include("nsot.api.urls")),
    # Catchall for missing endpoints
    re_path(r"^api/.*/$", NotFoundViewSet.as_view({"get": "list"})),
    # Docs
    path("schema.json", schema_view, name="swagger"),
    # Admin
    path("admin/", admin.site.urls),
    # Favicon redirect for when people insist on fetching it from /favicon.ico
    path(
        "favicon.ico",
        RedirectView.as_view(
            url="%sbuild/images/favicon/favicon.ico" % settings.STATIC_URL,
            permanent=True,
        ),
        name="favicon",
    ),
    # FE handlers
    # Catch index
    path("", FeView.as_view(), name="index"),
    # Catch all for remaining URLs
    re_path(r"^.*/$", FeView.as_view(), name="index"),
]
