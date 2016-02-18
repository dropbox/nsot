# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.conf import settings

from . import routers, views


# Register all endpoints as a top-level resource
router = routers.BulkRouter(trailing_slash=settings.APPEND_SLASH)

# Resources pinned to API index at /
router.register(r'sites', views.SiteViewSet)
router.register(r'attributes', views.AttributeViewSet)
router.register(r'changes', views.ChangeViewSet)
router.register(r'devices', views.DeviceViewSet)
router.register(r'interfaces', views.InterfaceViewSet)
router.register(r'networks', views.NetworkViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'values', views.ValueViewSet)

# Nested router for resources under /sites
sites_router = routers.BulkNestedRouter(
    router, r'sites', lookup='site', trailing_slash=settings.APPEND_SLASH
)

# Resources that are nested under /sites
sites_router.register(r'attributes', views.AttributeViewSet)
sites_router.register(r'changes', views.ChangeViewSet)
sites_router.register(r'devices', views.DeviceViewSet)
sites_router.register(r'interfaces', views.InterfaceViewSet)
sites_router.register(r'networks', views.NetworkViewSet)
sites_router.register(r'values', views.ValueViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # API routes
    url(r'^', include(router.urls)),
    url(r'^', include(sites_router.urls)),

    # Browsable API auth login
    url(r'^auth/', include('rest_framework.urls',
        namespace='rest_framework')),

    # API auth_token login/verify (email/secret_key)
    url(r'^authenticate/', views.AuthTokenLoginView.as_view(),
        name='authenticate'),
    url(r'^verify_token/', views.AuthTokenVerifyView.as_view(),
        name='verify_token'),
]
