from __future__ import unicode_literals

from collections import namedtuple, OrderedDict
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, ProtectedError
from django.shortcuts import render
import logging
from rest_framework import mixins, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework_bulk import mixins as bulk_mixins

from . import auth
from . import serializers
from .. import exc
from .. import models
from ..util import qpbool, parse_set_query


log = logging.getLogger(__name__)


class BaseNsotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Default viewset for Nsot objects with the following defaults:

    + Successful responses are in format ``{"status": "ok", "data": DATA}``
    + Error responses are in format ``{"status": "error", "error": ERROR}``
    + All list results always display pagination controls
    + Objects are designed to be nested under site resources, but can also be
      top-level resources.
    """
    def __init__(self, *args, **kwargs):
        super(BaseNsotViewSet, self).__init__(*args, **kwargs)

        # This is the model's human-readable name for results and error
        # messages.
        self.result_key = self.queryset.model._meta.model_name
        self.result_key_plural = self.result_key + 's'
        self.model_name = self.result_key.title()

    def not_found(self, pk=None, site_pk=None, msg=None):
        """Standard formatting for 404 errors."""
        if msg is None:
            msg = 'No such {} found at (site_id, id) = ({}, {})'.format(
                    self.model_name, site_pk, pk
                )
        raise exc.NotFound(msg)

    def success(self, data, result_key=None, status=200, headers=None):
        if result_key is None:
            # If there are multiple objects, use the plural result_key
            if isinstance(data, list):
                result_key = self.result_key_plural
            else:
                result_key = self.result_key

        return Response(
            OrderedDict([
                ('status', 'ok'),
                ('data', {result_key: data}),
            ]),
            status=status,
            headers=headers,
        )

    def get_paginated_response(self, data, result_key=None):
        """Overload default pagination to customize `result_key`."""
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, result_key)

    def create(self, request, *args, **kwargs):
        """Return objects that have just been created."""
        response = super(BaseNsotViewSet, self).create(request, *args, **kwargs)
        return self.success(
            response.data, status=response.status_code, headers=dict(response.items()),
        )

    def update(self, request, *args, **kwargs):
        """Return objects that have just been updated."""
        response = super(BaseNsotViewSet, self).update(request, *args, **kwargs)
        return self.success(response.data)

    def list(self, request, site_pk=None, queryset=None, *args, **kwargs):
        """List objects optionally filtered by site."""
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
            # Query by site_pk if it's set (.e.g /site/1/:foo) and make sure any
            # filtering args are passed.
            if site_pk is not None:
                queryset = queryset.filter(site=site_pk)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(
            data=serializer.data, result_key=self.result_key_plural
        )

    def retrieve(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Retrieve a single object optionally filtered by site."""
        try:
            if site_pk is not None:
                obj = self.queryset.get(pk=pk, site=site_pk)
            else:
                obj = self.queryset.get(pk=pk)
        except ObjectDoesNotExist:
            self.not_found(pk, site_pk)

        serializer = self.get_serializer(obj, *args, **kwargs)
        return self.success(serializer.data)


class ChangeViewSet(BaseNsotViewSet):
    """
    Read-only API endpoint that allows Changes to be viewed.

    All Create/Update/Delete events are logged as a Change. A Change includes
    information such as the change time, user, and the full resource after
    modification. Changes are immutable and can only be removed by deleting the
    entire Site.
    """
    queryset = models.Change.objects.order_by('-change_at')
    serializer_class = serializers.ChangeSerializer
    filter_fields = ('event', 'resource_name', 'resource_id')


class NsotViewSet(BaseNsotViewSet, viewsets.ModelViewSet):
    """
    Generic mutable viewset that logs all change events and includes support
    for bulk creation of objects.
    """
    def perform_create(self, serializer):
        """Support bulk create."""
        try:
            objects = serializer.save()
        except DjangoValidationError as err:
            raise exc.ValidationError(err.error_dict)
        except exc.IntegrityError as err:
            raise exc.Conflict(err.message)
        else:
            # This is so that we can always work w/ objects as a list
            if not isinstance(objects, list):
                objects = [objects]

        log.debug('NsotViewSet.perform_create() objects = %r', objects)
        for obj in objects:
            models.Change.objects.create(
                obj=obj, user=self.request.user, event='Create'
            )

    def get_success_headers(self, data):
        # TODO(jathan): Implement hyperlinked fields in the API?
        try:
            # return {'Location': data[api_settings.URL_FIELD_NAME]}
            location = '%s%s/' % (self.request.path_info, data['id'])
            return {'Location': location}
        except (TypeError, KeyError):
            return {}

    def perform_update(self, serializer):
        try:
            obj = serializer.save()
        except DjangoValidationError as err:
            raise exc.ValidationError(err.error_dict)
        except exc.IntegrityError as err:
            raise exc.Conflict(err.message)

        log.debug('NsotViewSet.perform_update() obj = %r', obj)
        models.Change.objects.create(
            obj=obj, user=self.request.user, event='Update'
        )

    def perform_destroy(self, instance):
        log.debug('NsotViewSet.perform_destroy() obj = %r', instance)
        models.Change.objects.create(
            obj=instance, user=self.request.user, event='Delete'
        )

        try:
            instance.delete()
        except ProtectedError as err:
            raise exc.Conflict(err.args[0])


class AttributeViewSet(NsotViewSet, bulk_mixins.BulkCreateModelMixin):
    """
    API endpoint that allows Attributes to be viewed or edited.
    """
    queryset = models.Attribute.objects.all()
    serializer_class = serializers.AttributeSerializer
    filter_fields = ('name', 'resource_name')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.AttributeCreateSerializer
        if self.request.method == 'PUT':
            return serializers.AttributeUpdateSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Filter the queryset based on query arguments.
        """
        # Only do this advanced query filtering when we're listing items.
        if self.request.method != 'GET':
            return super(AttributeViewSet, self).get_queryset()

        attributes = self.queryset

        params = self.request.query_params
        required = params.get('required', None)
        display = params.get('display', None)
        multi = params.get('multi', None)

        if required is not None:
            attributes = attributes.filter(required=qpbool(required))
        if display is not None:
            attributes = attributes.filter(display=qpbool(display))
        if multi is not None:
            attributes = attributes.filter(multi=qpbool(multi))

        return attributes


class ValueViewSet(NsotViewSet):
    """
    API endpoint that allows Attribute Values to be viewed or edited.
    """
    queryset = models.Value.objects.all()
    serializer_class = serializers.ValueSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.ValueCreateSerializer
        return self.serializer_class


class ResourceViewSet(NsotViewSet, bulk_mixins.BulkCreateModelMixin):
    """
    Resource views that include set query list endpoints.
    """
    @list_route(methods=['get'])
    def query(self, request, site_pk=None, *args, **kwargs):
        """Perform a set query."""
        query = request.query_params.get('query', '')

        objects = self.queryset.set_query(query, site_id=site_pk)
        return self.list(request, queryset=objects, *args, **kwargs)

    def get_resource_object(self, pk, site_pk):
        """Return a resource object based on pk or site_pk."""
        if site_pk is not None:
            query = self.queryset.filter(pk=pk, site=site_pk)
        else:
            query = self.queryset.filter(pk=pk)

        object = query.first()

        if not object:
            self.not_found(pk, site_pk)

        return object


class DeviceViewSet(ResourceViewSet):
    """
    API endpoint that allows Devices to be viewed or edited.
    """
    queryset = models.Device.objects.all()
    serializer_class = serializers.DeviceSerializer
    filter_fields = ('hostname',)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.DeviceCreateSerializer
        if self.request.method == 'PUT':
            return serializers.DeviceUpdateSerializer

        return self.serializer_class

    def get_queryset(self):
        """This is so we can filter by attribute/value pairs."""
        # Only do this advanced query filtering when we're listing items.
        if self.request.method != 'GET':
            return super(DeviceViewSet, self).get_queryset()

        devices = self.queryset

        params = self.request.query_params
        attributes = params.getlist('attributes', [])

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        log.debug('GOT ATTRIBUTES: %r', attributes)
        for attribute in attributes:
            name, _, value = attribute.partition('=')
            # Retrieve next set of networks using the same arguments as the
            # initial query.
            next_set = Q(
                attributes=models.Value.objects.filter(
                    attribute__name=name, value=value
                )
            )
            devices = devices.filter(next_set)

        return devices

    @detail_route(methods=['get'])
    def interfaces(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return all interfaces for this Device."""
        device = self.get_resource_object(pk, site_pk)
        interfaces = device.interfaces.all()
        self.result_key_plural = 'interfaces'

        return self.list(request, queryset=interfaces, *args, **kwargs)


class NetworkViewSet(ResourceViewSet):
    """
    API endpoint that allows Networks to be viewed or edited.
    """
    queryset = models.Network.objects.all()
    serializer_class = serializers.NetworkSerializer
    filter_fields = ('ip_version',)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.NetworkCreateSerializer
        if self.request.method == 'PUT':
            return serializers.NetworkUpdateSerializer

        return self.serializer_class

    @list_route(methods=['get'])
    def query(self, request, site_pk=None, *args, **kwargs):
        """Override base query to inherit filtering by query params."""
        self.queryset = self.get_queryset()
        return super(NetworkViewSet, self).query(
            request, site_pk, *args, **kwargs
        )

    def get_queryset(self):
        """
        Filter the queryset based on query arguments.
        """
        # Only do this advanced query filtering when we're listing items.
        if self.request.method != 'GET':
            return super(NetworkViewSet, self).get_queryset()

        networks = self.queryset

        params = self.request.query_params
        include_networks = qpbool(params.get('include_networks', True))
        include_ips = qpbool(params.get('include_ips', False))
        root_only = qpbool(params.get('root_only', False))
        cidr = params.get('cidr', None)
        attributes = params.getlist('attributes', [])
        network_address = params.get('network_address', None)
        prefix_length = params.get('prefix_length', None)

        if not any([include_networks, include_ips]):
            return networks.none()

        if not all([include_networks, include_ips]):
            if include_networks:
                networks = networks.filter(is_ip=False)
            if include_ips:
                networks = networks.filter(is_ip=True)

        if root_only:
            networks = networks.filter(parent=None)

        # If cidr is provided, use it to populate network_address and prefix_length
        if cidr is not None:
            log.debug('got cidr: %s' % cidr)
            network_address, _, prefix_length = cidr.partition('/')

        # If network_address is provided, pack it.
        if network_address is not None:
            log.debug('got network_address: %s' % network_address)
            networks = networks.filter(network_address=network_address)

        # If prefix_length is provided, convert it to an int.
        if prefix_length is not None:
            log.debug('got prefix_length: %s' % prefix_length)
            try:
                prefix_length = int(prefix_length)
            except ValueError:
                raise exc.BadRequest(
                    'Invalid prefix_length: %s' % prefix_length
                )
            networks = networks.filter(prefix_length=prefix_length)

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        log.debug('GOT ATTRIBUTES: %r', attributes)
        for attribute in attributes:
            name, _, value = attribute.partition('=')
            # Retrieve next set of networks using the same arguments as the
            # initial query.
            next_set = Q(
                attributes=models.Value.objects.filter(
                    attribute__name=name, value=value
                )
            )
            networks = networks.filter(next_set)

        return networks

    @detail_route(methods=['get'])
    def subnets(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return subnets of this Network."""
        network = self.get_resource_object(pk, site_pk)

        params = request.query_params
        include_networks = qpbool(params.get('include_networks', True))
        include_ips = qpbool(params.get('include_ips', False))
        direct = qpbool(params.get('direct', False))

        networks = network.subnets(
            include_networks=include_networks,
            include_ips=include_ips, direct=direct
        )

        return self.list(request, queryset=networks, *args, **kwargs)

    @detail_route(methods=['get'])
    def supernets(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return supernets of this Network."""
        network = self.get_resource_object(pk, site_pk)

        params = request.query_params
        direct = qpbool(params.get('direct', False))

        networks = network.supernets(direct=direct)

        return self.list(request, queryset=networks, *args, **kwargs)

    @detail_route(methods=['get'])
    def next_network(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return next available networks from this Network."""
        network = self.get_resource_object(pk, site_pk)

        params = request.query_params
        prefix_length = params.get('prefix_length')
        num = params.get('num')

        networks = network.get_next_network(
            prefix_length, num, as_objects=False
        )

        return self.success(networks, result_key='networks')

    @detail_route(methods=['get'])
    def next_address(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return next available IPs from this Network."""
        network = self.get_resource_object(pk, site_pk)

        num = request.query_params.get('num')
        addresses = network.get_next_address(num, as_objects=False)

        return self.success(addresses, result_key='addresses')

    @detail_route(methods=['get'])
    def ancestors(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return ancestors of this Network."""
        network = self.get_resource_object(pk, site_pk)
        ascending = qpbool(request.query_params.get('ascending', False))
        ancestors = network.get_ancestors(ascending=ascending)

        return self.list(request, queryset=ancestors, *args, **kwargs)

    @detail_route(methods=['get'])
    def children(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return the immediate children of this Network."""
        network = self.get_resource_object(pk, site_pk)
        children = network.get_children()

        return self.list(request, queryset=children, *args, **kwargs)

    @detail_route(methods=['get'])
    def descendents(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return descendents of this Network."""
        network = self.get_resource_object(pk, site_pk)
        descendents = network.get_descendents()

        return self.list(request, queryset=descendents, *args, **kwargs)

    @detail_route(methods=['get'])
    def parent(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return the parent of this Network."""
        network = self.get_resource_object(pk, site_pk)
        parent = network.parent
        if parent is not None:
            pk = network.parent_id
        else:
            pk = None

        return self.retrieve(request, pk, site_pk, *args, **kwargs)

    @detail_route(methods=['get'])
    def root(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return the parent of all ancestors for this Network."""
        network = self.get_resource_object(pk, site_pk)
        root = network.get_root()
        if root is not None:
            pk = root.id
        else:
            pk = None

        return self.retrieve(request, pk, site_pk, *args, **kwargs)

    @detail_route(methods=['get'])
    def siblings(self, request, pk=None, site_pk=None, *args, **kwargs):
        """
        Return Networks with the same parent. Root nodes are
        siblings to other root nodes.
        """
        network = self.get_resource_object(pk, site_pk)
        include_self = qpbool(request.query_params.get('include_self', False))
        descendents = network.get_siblings(include_self=include_self)

        return self.list(request, queryset=descendents, *args, **kwargs)


class InterfaceViewSet(ResourceViewSet):
    """
    API endpoint that allows Interfaces to be viewed or edited.
    """
    queryset = models.Interface.objects.all()
    serializer_class = serializers.InterfaceSerializer
    filter_fields = ('device', 'name', 'speed', 'type', 'description',
                     'parent_id')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.InterfaceCreateSerializer
        if self.request.method == 'PUT':
            return serializers.InterfaceUpdateSerializer

        return self.serializer_class

    @detail_route(methods=['get'])
    def addresses(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return a list of addresses for this Interface."""
        interface = self.get_resource_object(pk, site_pk)
        addresses = interface.addresses.all()
        self.result_key_plural = 'addresses'

        return self.list(request, queryset=addresses, *args, **kwargs)

    @detail_route(methods=['get'])
    def assignments(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return a list of information about my assigned addresses."""
        interface = self.get_resource_object(pk, site_pk)
        assignments = interface.assignments.all()
        self.result_key_plural = 'assignments'

        return self.list(request, queryset=assignments, *args, **kwargs)

    @detail_route(methods=['get'])
    def networks(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return all the containing Networks for my assigned addresses."""
        interface = self.get_resource_object(pk, site_pk)
        self.result_key_plural = 'networks'

        return self.list(request, queryset=interface.networks, *args, **kwargs)


class SiteViewSet(NsotViewSet):
    """
    API endpoint that allows Sites to be viewed or edited.
    """
    queryset = models.Site.objects.all()
    serializer_class = serializers.SiteSerializer
    filter_fields = ('name',)


#: Namedtuple for retrieving pk and user object of current user.
UserPkInfo = namedtuple('UserPkInfo', 'user pk')


class UserViewSet(BaseNsotViewSet, mixins.CreateModelMixin):
    """
    This viewset automatically provides `list` and `detail` actins.
    """
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer
    filter_fields = ('email',)

    def get_user_and_pk(self, request, pk=None, site_pk=None):
        # If pk is 0, return the current user.
        if int(pk) == 0:
            pk = request.user.pk  # Authenticated user

        # Try to get the requested user
        try:
            user = self.queryset.get(pk=pk)
        except ObjectDoesNotExist:
            self.not_found(pk, site_pk)

        return UserPkInfo(user, pk)

    def retrieve(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Retreive a single user."""
        user, pk = self.get_user_and_pk(request, pk, site_pk)

        params = request.query_params
        with_secret_key = params.get('with_secret_key', None)

        # If with_secret_key is set, confirm that the requested user object
        # matches the current user.
        if with_secret_key is not None:
            if user != request.user:
                raise exc.Forbidden(
                    "Can't access secret_key of user that isn't you."
                )
            kwargs['with_secret_key'] = qpbool(with_secret_key)

        return super(UserViewSet, self).retrieve(
            request, pk, site_pk, *args, **kwargs
        )

    @detail_route(methods=['post'])
    def rotate_secret_key(self, request, pk=None, *args, **kwargs):
        user, pk = self.get_user_and_pk(request, pk)

        if user != request.user:
            raise exc.Forbidden(
                "Can't access secret_key of user that isn't you."
        )

        user.rotate_secret_key()
        return self.success(user.secret_key, 'secret_key')


class NotFoundViewSet(viewsets.GenericViewSet):
    """Catchall for bad API endpoints."""
    def get(self, *args, **kwargs):
        raise exc.NotFound()

    def list(self, *args, **kwargs):
        raise exc.NotFound()

    def get_serializer_class(self):
        return None


class AuthTokenLoginView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = serializers.AuthTokenSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            data = {'auth_token': user.generate_auth_token()}

            return Response(
                OrderedDict([
                    ('status', 'ok'),
                    ('data', data),
                ])
            )
        raise exc.Unauthorized(serializer.errors)


class AuthTokenVerifyView(APIView):
    authentication_classes = (auth.AuthTokenAuthentication,)
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        return Response(
            OrderedDict([
                ('status', 'ok'),
                ('data', True),
            ])
        )
