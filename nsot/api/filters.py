from __future__ import unicode_literals
import logging

from django.db.models import Q
import django_filters  # django-filters is NOT optional for NSoT
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
        resource_name = queryset.model.__name__

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        log.debug('GOT ATTRIBUTES: %r', attributes)

        for attribute in attributes:
            name, _, value = attribute.partition('=')
            # Retrieve next set of objects using the same arguments as the
            # initial query.
            next_set = Q(
                id__in=models.Value.objects.filter(
                    name=name, value=value, resource_name=resource_name
                ).values_list('resource_id', flat=True)
            )
            queryset = queryset.filter(next_set)

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
        include_ips = qpbool(self.form.cleaned_data['include_ips'])
        include_networks = qpbool(value)

        if not all([include_networks, include_ips]):
            if include_networks:
                return queryset.filter(is_ip=False)
            else:
                return queryset.exclude(is_ip=False)

        return queryset

    def filter_include_ips(self, queryset, value):
        """Converts ``include_ips`` to queryset filters."""
        include_ips = qpbool(value)
        include_networks = qpbool(self.form.cleaned_data['include_networks'])

        if not all([include_networks, include_ips]):
            if include_ips:
                return queryset.filter(is_ip=True)
            else:
                return queryset.exclude(is_ip=True)

        return queryset

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


class InterfaceFilter(ResourceFilter):
    """
    Filter for Interface objects.

    Includes a custom override for filtering on mac_address because this is not
    a Django built-in field.
    """
    mac_address = django_filters.MethodFilter()

    class Meta:
        model = models.Interface
        fields = [
            'device', 'device__hostname', 'name', 'speed', 'type',
            'mac_address', 'description', 'parent_id', 'attributes'
        ]

    def filter_mac_address(self, queryset, value):
        """
        Overloads queryset filtering to use built-in.

        Doesn't work by default because MACAddressField is not a Django
        built-in field type.
        """
        return queryset.filter(mac_address=value)
