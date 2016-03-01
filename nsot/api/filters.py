from __future__ import unicode_literals

import django_filters  # django-filters is NOT optional for NSoT
import logging
from rest_framework import filters

from .. import models
from ..util import qpbool


log = logging.getLogger(__name__)


class ResourceFilter(filters.FilterSet):
    """Attribute-aware filtering for Resource objects."""
    attributes = django_filters.MethodFilter()

    def filter_attributes(self, queryset, value):
        """
        Reads 'attributes' from query params and joins them together as an
        intersection set query.
        """
        attributes = self.data.getlist('attributes', [])

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        log.debug('GOT ATTRIBUTES: %r', attributes)

        set_query = ' '.join(attributes)
        if set_query:
            queryset = queryset.set_query(set_query)

        return queryset


class DeviceFilter(ResourceFilter):
    """Filter for Device objects."""
    class Meta:
        model = models.Device
        fields = ['hostname', 'attributes']


class NetworkFilter(ResourceFilter):
    """Filter for Network objects."""
    include_networks = django_filters.MethodFilter()
    include_ips = django_filters.MethodFilter()
    network_address = django_filters.CharFilter()
    cidr = django_filters.MethodFilter()
    root_only = django_filters.MethodFilter()

    class Meta:
        model = models.Network
        fields = [
            'include_networks', 'include_ips', 'root_only', 'cidr',
            'network_address', 'prefix_length', 'ip_version', 'state',
            'attributes'
        ]

    def filter_include_networks(self, queryset, value):
        """Converts ``include_networks`` to queryset filters."""
        if qpbool(value):
            return queryset.filter(is_ip=False)
        else:
            return queryset.exclude(is_ip=False)

    def filter_include_ips(self, queryset, value):
        """Converts ``include_ips`` to queryset filters."""
        if qpbool(value):
            return queryset.filter(is_ip=True)
        else:
            return queryset.exclude(is_ip=True)

    def filter_cidr(self, queryset, value):
        """Converts ``cidr`` to network/prefix filter."""
        if value:
            network_address, _, prefix_length = value.partition('/')
        else:
            return queryset

        return queryset.filter(
            network_address=network_address,
            prefix_length=prefix_length
        )

    def filter_root_only(self, queryset, value):
        """Converts ``root_only`` to null parent filter."""
        if qpbool(value):
            return queryset.filter(parent=None)
        return queryset
