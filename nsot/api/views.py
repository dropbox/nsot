from __future__ import unicode_literals
from collections import namedtuple, OrderedDict
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework_bulk import mixins as bulk_mixins
from rest_framework_extensions.cache.decorators import cache_response

from . import auth, filters, serializers
from .. import exc, models
from ..util import cache, qpbool, cidr_to_dict


log = logging.getLogger(__name__)


class BaseNsotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Default viewset for Nsot objects with the following defaults:

    + Objects are designed to be nested under site resources, but can also be
      top-level resources.
    """

    #: Natural key for the resource. If not defined, defaults to pk-only.
    natural_key = None

    @property
    def model_name(self):
        return self.queryset.model.__name__

    def get_natural_key_kwargs(self, filter_value):
        """
        This method should take value and return a dictionary containing the
        natural key fields used to filter results.

        This is called internally by ``self.get_object()`` if a subclass has
        defined a ``natural_key``.

        :param filter_value:
            Value to be used to filter by natural_key
        """
        raise NotImplementedError('This must be defined in a subclass.')

    def not_found(self, pk=None, site_pk=None, msg=None):
        """Standard formatting for 404 errors."""
        if msg is None:
            msg = 'No such {} found at (site_id, id) = ({}, {})'.format(
                self.model_name, site_pk, pk
            )
        raise exc.NotFound(msg)

    def success(self, data, status=200, headers=None):
        return Response(data, status=status, headers=headers)

    def list(self, request, site_pk=None, queryset=None, *args, **kwargs):
        """List objects optionally filtered by site."""
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
            # Query by site_pk if it's set (e.g. /sites/1/:foo) and make sure
            # any filtering args are passed.
            if site_pk is not None:
                queryset = queryset.filter(site=site_pk)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return super(BaseNsotViewSet, self).get_paginated_response(
                serializer.data
            )

        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)

    def retrieve(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Retrieve a single object optionally filtered by site."""
        # If the incoming pk has changed, store it in view kwargs. This is so
        # that nested routers and detail routes work properly such as when
        # calling ``GET /api/sites/1/networks/40/parent/``.
        if 'pk' in self.kwargs:
            self.kwargs['pk'] = pk
        if 'site_pk' in self.kwargs:
            self.kwargs['site_pk'] = site_pk

        obj = self.get_object()
        serializer = self.get_serializer(obj, *args, **kwargs)

        return self.success(serializer.data)

    def get_object(self):
        """
        Enhanced default to support looking up objects for:

        + Natural key lookups for resource objects (e.g. Device.hostname)
        + Inject of ``site`` into filter lookup if ``site_pk`` is set.

        Currently this does NOT filter the queryset, which should not be a
        problem as we were never using .get_object() before. See the FIXME
        comments for more context.
        """
        # FIXME(jathan): Determine if we actually need .filter_queryset() here
        # queryset = self.filter_queryset(self.get_queryset())

        # FIXME(jathan): Determine if we actually need .get_queryset() here.
        # Given the way things are implemented w/ the custom .get_queryset()
        # methods for default GET filtering, we might not need to use it.
        # queryset = self.get_queryset()

        queryset = self.queryset

        # Retrieve the pk, site_pk args from the view's kwargs.
        site_pk = self.kwargs.get('site_pk')
        pk = self.kwargs.get('pk')

        # When coming from detail routes, pk might not be a string.
        if isinstance(pk, (int, long)):
            pk = str(pk)

        # Start prepping our kwargs for lookup.
        lookup_kwargs = {}
        if site_pk is not None:
            lookup_kwargs['site'] = site_pk

        # If pk is null, is a digit, or if we don't have a natural_key, lookup
        # by pk.
        if pk is None or pk.isdigit() or self.natural_key is None:
            lookup_kwargs['pk'] = pk

        # Otherwise prepare the natural_key for a single object lookup.
        else:
            natural_kwargs = self.get_natural_key_kwargs(pk)
            lookup_kwargs.update(natural_kwargs)

        # Try to get a single object.
        try:
            obj = queryset.get(**lookup_kwargs)
        except exc.ObjectDoesNotExist:
            self.not_found(pk, site_pk)
        # This may happen if:
        # - You've got multiple sites and an object w/ the same natural_key in
        #   different Sites. For example: Device 'foo-bar1' in Site 1 and
        #   Device 'foo-bar1' in Site 2.
        # - You're not using a site-specific end-point (e.g. /api/devices/ vs.
        #   /api/sites/1/devices/).
        except exc.MultipleObjectsReturned:
            raise exc.ValidationError(
                'Multiple %ss matched %s=%r. Use a site-specific endpoint '
                'or lookup by ID.' % (
                    self.model_name, self.natural_key, pk
                )
            )

        # May raise a permission denied.
        self.check_object_permissions(self.request, obj)

        return obj


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
        """Support bulk create.

        :param serializer:
            Serializer instance
        """
        try:
            objects = serializer.save()
        except exc.DjangoValidationError as err:
            raise exc.ValidationError(err.message_dict)
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
        """
        Overload default to include relative request PATH.

        :param data:
            Dict of validated serializer data
        """
        # TODO(jathan): Implement hyperlinked fields in the API?
        try:
            # return {'Location': data[api_settings.URL_FIELD_NAME]}
            location = '%s%s/' % (self.request.path_info, data['id'])
            return {'Location': location}
        except (TypeError, KeyError):
            return {}

    def perform_update(self, serializer):
        """
        Overload default to handle non-serializer exceptions, and log Change
        events.

        :param serializer:
            Serializer instance
        """
        try:
            objects = serializer.save()
        except exc.DjangoValidationError as err:
            raise exc.ValidationError(err.message_dict)
        except exc.IntegrityError as err:
            raise exc.Conflict(err.message)
        else:
            # This is so that we can always work w/ objects as a list
            if not isinstance(objects, list):
                objects = [objects]

        log.debug('NsotViewSet.perform_update() objects = %r', objects)
        for obj in objects:
            models.Change.objects.create(
                obj=obj, user=self.request.user, event='Update'
            )

    def perform_destroy(self, instance):
        """
        Overload default to handle non-serializer exceptions, and log Change
        events.

        :param instance:
            Model instance to delete
        """
        log.debug('NsotViewSet.perform_destroy() obj = %r', instance)
        change = models.Change.objects.create(
            obj=instance, user=self.request.user, event='Delete'
        )

        try:
            instance.delete()
        except exc.ProtectedError as err:
            change.delete()
            raise exc.Conflict(err.args[0])


class SiteViewSet(NsotViewSet):
    """
    API endpoint that allows Sites to be viewed or edited.
    """
    queryset = models.Site.objects.all()
    serializer_class = serializers.SiteSerializer
    filter_fields = ('name',)


class ValueViewSet(NsotViewSet):
    """
    API endpoint that allows Attribute Values to be viewed or edited.
    """
    queryset = models.Value.objects.all()
    serializer_class = serializers.ValueSerializer
    filter_fields = ('name', 'value', 'resource_name', 'resource_id')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.ValueCreateSerializer
        return self.serializer_class


class NsotBulkUpdateModelMixin(bulk_mixins.BulkUpdateModelMixin):
    """
    The default mixin isn't using super() so multiple-inheritance breaks. This
    fixes it for our use-case.
    """
    def perform_update(self, serializer):
        super(bulk_mixins.BulkUpdateModelMixin, self).perform_update(
            serializer
        )


class ResourceViewSet(NsotBulkUpdateModelMixin, NsotViewSet,
                      bulk_mixins.BulkCreateModelMixin):
    """
    Resource views that include set query list endpoints.
    """

    @list_route(methods=['get'])
    def query(self, request, site_pk=None, *args, **kwargs):
        """Perform a set query."""
        query = request.query_params.get('query', '')

        qs = self.queryset.set_query(query, site_id=site_pk)
        objects = self.filter_queryset(qs)
        return self.list(request, queryset=objects, *args, **kwargs)

    def get_resource_object(self, pk, site_pk):
        """Return a resource object based on pk or site_pk."""
        # FIXME(jathan): Revisit this after we've seen if we can need to get
        # rid of the overloaded .get_queryset() methods on the ResourceViewSet
        # subclasses, or provide them with some sort of "don't filter queries"
        # flag. TBD.

        # Backup the original kwargs
        orig_kwargs = self.kwargs.copy()
        self.kwargs['pk'] = pk
        self.kwargs['site_pk'] = site_pk

        # Get our object and restore the original kwargs
        obj = self.get_object()
        self.kwargs = orig_kwargs

        return obj


class AttributeViewSet(ResourceViewSet):
    """
    API endpoint that allows Attributes to be viewed or edited.
    """
    queryset = models.Attribute.objects.all()
    serializer_class = serializers.AttributeSerializer
    filter_fields = ('name', 'resource_name', 'required', 'display', 'multi')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.AttributeCreateSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return serializers.AttributeUpdateSerializer
        return self.serializer_class


class DeviceViewSet(ResourceViewSet):
    """
    API endpoint that allows Devices to be viewed or edited.
    """
    queryset = models.Device.objects.all()
    serializer_class = serializers.DeviceSerializer
    filter_class = filters.DeviceFilter
    natural_key = 'hostname'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.DeviceCreateSerializer
        if self.request.method == 'PUT':
            return serializers.DeviceUpdateSerializer
        if self.request.method == 'PATCH':
            return serializers.DevicePartialUpdateSerializer

        return self.serializer_class

    def get_natural_key_kwargs(self, filter_value):
        """Return a dict of kwargs for natural_key lookup."""
        return {self.natural_key: filter_value}

    @detail_route(methods=['get'])
    def interfaces(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return all interfaces for this Device."""
        device = self.get_resource_object(pk, site_pk)
        interfaces = device.interfaces.all()

        return self.list(request, queryset=interfaces, *args, **kwargs)


class NetworkViewSet(ResourceViewSet):
    """
    API endpoint that allows Networks to be viewed or edited.
    """
    queryset = models.Network.objects.all()
    serializer_class = serializers.NetworkSerializer
    filter_class = filters.NetworkFilter
    lookup_value_regex = '[a-fA-F0-9:.]+(?:\/\d+)?'
    natural_key = 'cidr'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.NetworkCreateSerializer
        if self.request.method == 'PUT':
            return serializers.NetworkUpdateSerializer
        if self.request.method == 'PATCH':
            return serializers.NetworkPartialUpdateSerializer

        return self.serializer_class

    def get_natural_key_kwargs(self, filter_value):
        """Return a dict of kwargs for natural_key lookup."""
        return cidr_to_dict(filter_value)

    @list_route(methods=['get'])
    def query(self, request, site_pk=None, *args, **kwargs):
        """Override base query to inherit filtering by query params."""
        self.queryset = self.get_queryset()
        return super(NetworkViewSet, self).query(
            request, site_pk, *args, **kwargs
        )

    @detail_route(methods=['get'])
    def closest_parent(self, request, pk=None, site_pk=None, *args, **kwargs):
        """
        Return the closest matching parent of this Network even if it doesn't
        exist in the database.
        """
        prefix_length = request.query_params.get('prefix_length', 0)

        # Get closest parent or 404
        try:
            network = models.Network.objects.get_closest_parent(
                pk, prefix_length=prefix_length, site=site_pk
            )
        except models.Network.DoesNotExist:
            self.not_found(pk, site_pk)
        else:
            pk = network.id  # Use the id of the network we found

        return self.retrieve(request, pk, site_pk, *args, **kwargs)

    @detail_route(methods=['get'])
    def subnets(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return subnets of this Network."""
        network = self.get_resource_object(pk, site_pk)

        params = request.query_params
        include_networks = qpbool(params.get('include_networks', True))
        include_ips = qpbool(params.get('include_ips', True))
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

        return self.success(networks)

    @detail_route(methods=['get'])
    def next_address(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return next available IPs from this Network."""
        network = self.get_resource_object(pk, site_pk)

        num = request.query_params.get('num')
        addresses = network.get_next_address(num, as_objects=False)

        return self.success(addresses)

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

    @detail_route(methods=['get'])
    def assignments(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return the interface assignments for this Network."""
        network = self.get_resource_object(pk, site_pk)
        assignments = network.assignments.all()

        return self.list(request, queryset=assignments, *args, **kwargs)

    @list_route(methods=['get'])
    def reserved(self, request, site_pk=None, *args, **kwargs):
        """Display all reserved Networks."""
        objects = models.Network.objects.reserved()
        return self.list(request, queryset=objects, *args, **kwargs)


class InterfaceViewSet(ResourceViewSet):
    """
    API endpoint that allows Interfaces to be viewed or edited.
    """
    queryset = models.Interface.objects.all()
    serializer_class = serializers.InterfaceSerializer
    filter_class = filters.InterfaceFilter

    @cache_response(cache_errors=False, key_func=cache.list_key_func)
    def list(self, *args, **kwargs):
        """Override default list so we can cache results."""
        return super(InterfaceViewSet, self).list(*args, **kwargs)

    @cache_response(cache_errors=False, key_func=cache.object_key_func)
    def retrieve(self, *args, **kwargs):
        """Override default retrieve so we can cache results."""
        return super(InterfaceViewSet, self).retrieve(*args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.InterfaceCreateSerializer
        if self.request.method == 'PUT':
            return serializers.InterfaceUpdateSerializer
        if self.request.method == 'PATCH':
            return serializers.InterfacePartialUpdateSerializer

        return self.serializer_class

    @detail_route(methods=['get'])
    def addresses(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return a list of addresses for this Interface."""
        interface = self.get_resource_object(pk, site_pk)
        addresses = interface.addresses.all()

        return self.list(request, queryset=addresses, *args, **kwargs)

    @detail_route(methods=['get'])
    def assignments(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return a list of information about my assigned addresses."""
        interface = self.get_resource_object(pk, site_pk)
        assignments = interface.assignments.all()

        return self.list(request, queryset=assignments, *args, **kwargs)

    @detail_route(methods=['get'])
    def networks(self, request, pk=None, site_pk=None, *args, **kwargs):
        """Return all the containing Networks for my assigned addresses."""
        interface = self.get_resource_object(pk, site_pk)

        return self.list(request, queryset=interface.networks, *args, **kwargs)


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
        except exc.ObjectDoesNotExist:
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
        return self.success(user.secret_key)


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

            if request.version == settings.NSOT_API_VERSION:
                return Response(data)

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
        if request.version == settings.NSOT_API_VERSION:
            return Response(True)

        return Response(
            OrderedDict([
                ('status', 'ok'),
                ('data', True),
            ])
        )
