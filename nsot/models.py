# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from calendar import timegm
from cryptography.fernet import (Fernet, InvalidToken)
from custom_user.models import AbstractEmailUser
from django.db import models
from django.db.models.query_utils import Q
from django.conf import settings
from django.core.cache import cache as djcache
from django.utils import timezone
import ipaddress
import json
import logging
import netaddr
from operator import attrgetter
import re

from . import exc
from . import fields
from . import validators
from .util import cidr_to_dict, generate_secret_key, parse_set_query, stats


log = logging.getLogger(__name__)

# These are constants that becuase they are tied directly to the underlying
# objects are explicitly NOT USER CONFIGURABLE.
RESOURCE_BY_IDX = (
    'Site', 'Network', 'Attribute', 'Device', 'Interface'
)
RESOURCE_BY_NAME = {
    obj_type: idx
    for idx, obj_type in enumerate(RESOURCE_BY_IDX)
}

CHANGE_EVENTS = ('Create', 'Update', 'Delete')

VALID_CHANGE_RESOURCES = set(RESOURCE_BY_IDX)
VALID_ATTRIBUTE_RESOURCES = set([
    'Network', 'Device', 'Interface'
])

# Lists of 2-tuples of (value, option) for displaying choices in certain model
# serializer/form fields.
CHANGE_RESOURCE_CHOICES = [(c, c) for c in VALID_CHANGE_RESOURCES]
EVENT_CHOICES = [(c, c) for c in CHANGE_EVENTS]
IP_VERSION_CHOICES = [(c, c) for c in settings.IP_VERSIONS]
RESOURCE_CHOICES = [(c, c) for c in VALID_ATTRIBUTE_RESOURCES]

# Unique interface type IDs.
INTERFACE_TYPES = [t[0] for t in settings.INTERFACE_TYPE_CHOICES]


class Site(models.Model):
    """A namespace for attribtues, devices, and networks."""
    name = models.CharField(
        max_length=255, unique=True, help_text='The name of the Site.'
    )
    description = models.TextField(
        default='', blank=True, help_text='A helpful description for the Site.'
    )

    def __unicode__(self):
        return self.name

    def clean_name(self, value):
        return validators.validate_name(value)

    def clean_fields(self, exclude=None):
        self.name = self.clean_name(self.name)

    def save(self, *args, **kwargs):
        self.full_clean()  # First validate fields are correct
        super(Site, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


class User(AbstractEmailUser):
    """A custom user object that utilizes email as the username."""
    secret_key = models.CharField(
        max_length=44, default=generate_secret_key,
        help_text="The user's secret_key used for API authentication."
    )

    @property
    def username(self):
        return self.get_username()

    def get_permissions(self):
        permissions = []
        if self.is_staff or self.is_superuser:
            permissions.append('admin')
        sites = Site.objects.all()

        return {
            str(site.id): {
                'permissions': permissions,
                'site_id': site.id,
                'user_id': self.id
            }
            for site in sites
        }

    def rotate_secret_key(self):
        self.secret_key = generate_secret_key()
        self.save()

    def generate_auth_token(self):
        """Serialize user data and encrypt token."""
        # Serialize data
        data = json.dumps({'email': self.email})

        # Encrypt w/ servers's secret_key
        f = Fernet(bytes(settings.SECRET_KEY))
        auth_token = f.encrypt(bytes(data))
        return auth_token

    def verify_secret_key(self, secret_key):
        """Validate secret_key"""
        return secret_key == self.secret_key

    @classmethod
    def verify_auth_token(cls, email, auth_token, expiration=None):
        """Verify token and return a User object."""
        if expiration is None:
            expiration = settings.AUTH_TOKEN_EXPIRY

        # First we lookup the user by email
        query = cls.objects.filter(email=email)
        user = query.first()

        if user is None:
            log.debug('Invalid user when verifying token')
            raise exc.ValidationError({
                'auth_token': 'Invalid user when verifying token'
            })
            # return None  # Invalid user

        # Decrypt auth_token w/ user's secret_key
        f = Fernet(bytes(settings.SECRET_KEY))
        try:
            decrypted_data = f.decrypt(bytes(auth_token), ttl=expiration)
        except InvalidToken:
            log.debug('Invalid/expired auth_token when decrypting.')
            raise exc.ValidationError({
                'auth_token': 'Invalid/expired auth_token.'
            })
            # return None  # Invalid token

        # Deserialize data
        try:
            data = json.loads(decrypted_data)
        except ValueError:
            log.debug('Token could not be deserialized.')
            raise exc.ValidationError({
                'auth_token': 'Token could not be deserialized.'
            })
            # return None  # Valid token, but expired

        if email != data['email']:
            log.debug('Invalid user when deserializing.')
            raise exc.ValidationError({
                'auth_token': 'Invalid user when deserializing.'
            })
            # return None  # User email did not match payload
        return user

    def clean_email(self, value):
        return validators.validate_email(value)

    def clean_fields(self, exclude=None):
        self.email = self.clean_email(self.email)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(User, self).save(*args, **kwargs)

    def to_dict(self, with_permissions=False, with_secret_key=False):
        out = [
            ('id', self.id),
            ('email', self.email),
        ]

        if with_secret_key:
            out.append(('secret_key', self.secret_key))

        if with_permissions:
            out.append(('permissions', self.get_permissions()))

        return dict(out)


class ResourceSetTheoryQuerySet(models.query.QuerySet):
    """
    Set theory QuerySet for Resource objects to add ``.set_query()`` method.

    For example::

        >>> qs = Network.objects.filter(network_address=u'10.0.0.0')
        >>> qs.set_query('owner=jathan +metro=lax')

    You may also search using regex by appending ``_regex`` to an attribtue
    name and providing a regex pattern as the value::

        >>> qs = Device.objects.set_query('role_regex=[bd]r')

    Which is functionally equivalent to::

        >>> qs = Device.objects.set_query('role=br +role=dr')
    """
    def set_query(self, query, site_id=None):
        """
        Filter objects by set theory attribute-value ``query`` patterns.
        """
        objects = self
        if site_id is not None:
            objects = objects.filter(site=site_id)

        try:
            attributes = parse_set_query(query)
        except (ValueError, TypeError) as err:
            raise exc.ValidationError({
                'query': err.message
            })

        # If there aren't any parsed attributes, don't return anything.
        if not attributes:
            return objects.none()

        resource_name = self.model.__name__

        # Iterate a/v pairs and combine query results using MySQL-compatible
        # set operations w/ the ORM
        log.debug('QUERY [start]: objects = %r', objects)
        for action, name, value in attributes:
            # Is this a regex pattern?
            regex_query = False
            if name.endswith('_regex'):
                name = name.replace('_regex', '')  # Keep attribute name
                regex_query = True
                log.debug('Regex enabled for %r' % name)

            # Attribute lookup params
            params = dict(
                name=name, resource_name=resource_name
            )
            # Only include site_id if it's set
            if site_id is not None:
                params['site_id'] = site_id

            # If an Attribute doesn't exist, the set query is invalid. Return
            # an empty queryset. (fix #99)
            try:
                attr = Attribute.objects.get(
                    **params
                )
            except Attribute.DoesNotExist as err:
                raise exc.ValidationError({
                    'query': '%s: %r' % (err.message.rstrip('.'), name)
                })

            # Set lookup params
            next_set_params = {
                'name': attr.name,
                'value': value,
                'resource_name': resource_name
            }

            # If it's a regex query, swap ``value`` with ``value__regex``.
            if regex_query:
                next_set_params['value__regex'] = next_set_params.pop('value')

            next_set = Q(
                id__in=Value.objects.filter(
                    **next_set_params
                ).values_list('resource_id', flat=True)
            )

            # This is the MySQL-compatible manual implementation of set theory,
            # baby!
            if action == 'union':
                log.debug('SQL UNION')
                objects = (
                    objects | self.filter(next_set)
                )
            elif action == 'difference':
                log.debug('SQL DIFFERENCE')
                objects = objects.exclude(next_set)
            elif action == 'intersection':
                log.debug('SQL INTERSECTION')
                objects = objects.filter(next_set)
            else:
                raise exc.BadRequest('BAD SET QUERY: %r' % (action,))
            log.debug('QUERY [iter]: objects = %r', objects)

        # Gotta call .distinct() or we might get dupes.
        return objects.distinct()

    def by_attribute(self, name, value, site_id=None):
        """
        Lookup objects by Attribute ``name`` and ``value``.
        """
        resource_name = self.model._meta.model_name.title()
        query = self.filter(
            id__in=Value.objects.filter(
                name=name, value=value, resource_name=resource_name
            ).values_list('resource_id', flat=True)
        )

        if site_id is not None:
            query = query.filter(site=site_id)

        return query


class ResourceManager(models.Manager):
    """
    Manager for Resource objects that adds a special resource methods:

    + ``.set_query()`` - For performing set theory lookups by attribute-value
      string patterns
    + ``.by_attribute()`` - For looking up objects by attribute name/value.

    """
    queryset_class = ResourceSetTheoryQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db)

    def set_query(self, query, site_id=None):
        """
        Filter objects by set theory attribute-value string patterns.

        For example::

            >>> Network.objects.set_query('owner=jathan +metro=lax'}
            [<Device: foo-bar1>]

        :param query:
            Set theory query pattern

        :param site_id:
            ID of Site to filter results
        """
        return self.get_queryset().set_query(query, site_id)

    def by_attribute(self, name, value, site_id=None):
        """
        Filter objects by Attribute ``name`` and ``value``.

        For example::

            >>> Interface.objects.by_attribute(name='vlan', value=300)
            [<Interface: device=1, name=eth0>]

        :param name:
            Attribute name

        :param value:
            Attribute value

        :param site_id:
            ID of Site to filter results
        """
        return self.get_queryset().by_attribute(name, value, site_id)


class Resource(models.Model):
    """Base for heirarchial Resource objects that may have attributes."""
    _attributes_cache = fields.JSONField(
        null=False, blank=True,
        help_text='Local cache of attributes. (Internal use only)'
    )

    def __init__(self, *args, **kwargs):
        self._set_attributes = kwargs.pop('attributes', None)
        super(Resource, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True

    # Implement .objects.set_query()
    objects = ResourceManager()

    @property
    def attributes(self):
        return Value.objects.filter(
            resource_name=self._resource_name, resource_id=self.id
        )

    @property
    def _resource_name(self):
        return self.__class__.__name__

    def _purge_attribute_index(self):
        self.attributes.all().delete()

    def get_attributes(self):
        """Return the JSON-encoded attributes as a dict."""
        return self._attributes_cache

    def set_attributes(self, attributes, valid_attributes=None, partial=False):
        """Validate and store the attributes dict as a JSON-encoded string."""
        log.debug('Resource.set_attributes() attributes = %r',
                  attributes)

        # If no attributes and it's a partial update, NOOP.
        if attributes is None and partial:
            return None

        if not isinstance(attributes, dict):
            raise exc.ValidationError({
                'attributes': 'Expected dictionary but received {}'.format(
                    type(attributes)
                )
            })

        # A dict of valid Attribute objects for this resource, keyed by
        # attribute name. If not provided, defaults to all matching
        # resource_name.
        if valid_attributes is None:
            valid_attributes = Attribute.all_by_name(
                self._resource_name, self.site
            )
        log.debug('Resource.set_attributes() valid_attributes = %r',
                  valid_attributes)

        # Attributes that are required according to ``valid_attributes``, but
        # are not found incoming in ``attributes``.
        missing_attributes = {
            attribute.name for attribute in valid_attributes.itervalues()
            if attribute.required and attribute.name not in attributes
        }
        log.debug('Resource.set_attributes() missing_attributes = %r',
                  missing_attributes)

        # It's an error to have any missing attributes
        if missing_attributes:
            names = ', '.join(missing_attributes)
            raise exc.ValidationError({
                'attributes': 'Missing required attributes: {}'.format(names)
            })

        # Run validation each attribute value and prepare them for DB
        # insertion, raising any validation errors immediately.
        inserts = []
        for name, value in attributes.iteritems():
            if name not in valid_attributes:
                raise exc.ValidationError({
                    'attributes': 'Attribute name ({}) does not exist.'.format(
                        name
                    )
                })

            if not isinstance(name, basestring):
                raise exc.ValidationError({
                    'attributes': 'Attribute names must be a string type.'
                })

            attribute = valid_attributes[name]
            inserts.extend(attribute.validate_value(value))

        # Purge all of our previously existing attribute values and recreate
        # them anew. This isn't exactly efficient.
        self._purge_attribute_index()
        for insert in inserts:
            Value.objects.create(
                obj=self, attribute_id=insert['attribute_id'],
                value=insert['value']
            )

        self.clean_attributes()

    def clean_attributes(self):
        """Make sure that attributes are saved as JSON."""
        attrs = {}

        # Only fetch the fields we need.
        for a in self.attributes.only('name', 'value', 'attribute').iterator():
            if a.attribute.multi:
                if a.name not in attrs:
                    attrs[a.name] = []
                attrs[a.name].append(a.value)
            else:
                attrs[a.name] = a.value
        self._attributes_cache = attrs  # Cache the attributes

        return attrs

    def save(self, *args, **kwargs):
        self._is_new = self.id is None  # Check if this is a new object.
        super(Resource, self).save(*args, **kwargs)

        # This is so that we can set the attributes on create/update, but if
        # the object is new, make sure that it doesn't persist if attributes
        # fail.
        if self._set_attributes is not None:
            try:
                # And set the attributes (if any)
                self.set_attributes(self._set_attributes)
            except exc.ValidationError:
                # If attributes fail validation, and I'm a new object, delete
                # myself and re-raise the error.
                if self._is_new:
                    self.delete()
                raise


class Device(Resource):
    """Represents a network device."""
    hostname = models.CharField(
        max_length=255, null=False, db_index=True,
        help_text='The hostname of the Device.'
    )
    site = models.ForeignKey(
        Site, db_index=True, related_name='devices', on_delete=models.PROTECT,
        verbose_name='Site',
        help_text='Unique ID of the Site this Device is under.'
    )

    def __unicode__(self):
        return u'%s' % self.hostname

    class Meta:
        unique_together = ('site', 'hostname')
        index_together = unique_together

    def clean_hostname(self, value):
        if not value:
            raise exc.ValidationError({
                'hostname': 'Hostname must be non-zero length string.'
            })
        if not settings.DEVICE_NAME.match(value):
            raise exc.ValidationError({
                'name': 'Invalid name: %r.' % value
            })
        return value

    def clean_fields(self, exclude=None):
        self.hostname = self.clean_hostname(self.hostname)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Device, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'site_id': self.site_id,
            'hostname': self.hostname,
            'attributes': self.get_attributes(),
        }


class NetworkManager(ResourceManager):
    """Manager for NetworkInterface objects."""
    def get_by_address(self, cidr, site=None):
        """
        Lookup a Network object by ``cidr``.

        :param cidr:
            IPv4/IPv6 CIDR string

        :param site:
            ``Site`` instance or ``site_id``
        """
        lookup_kwargs = cidr_to_dict(cidr)
        if site is not None:
            lookup_kwargs['site'] = site

        address = Network.objects.get(**lookup_kwargs)
        return address

    def get_closest_parent(self, cidr, prefix_length=0, site=None):
        """
        Return the closest matching parent Network for a ``cidr`` even if it
        doesn't exist in the database.

        :param cidr:
            IPv4/IPv6 CIDR string

        :param prefix_length:
            Maximum prefix length depth for closest parent lookup

        :param site:
            ``Site`` instance or ``site_id``
        """
        # Validate that it's a real CIDR
        cidr = validators.validate_cidr(cidr)
        broadcast_address = cidr.broadcast_address.exploded
        leaf = netaddr.IPNetwork(str(cidr))
        ip_version = leaf.version

        try:
            prefix_length = int(prefix_length)
        except ValueError:
            raise exc.ValidationError({
                'prefix_length': 'Invalid prefix_length: %r' %
                prefix_length
            })

        # Walk the supernets backwrds from smallest to largest prefix.
        try:
            supernets = leaf.supernet(prefixlen=prefix_length)
        except ValueError as err:
            raise exc.ValidationError({
                'prefix_length': err.message
            })
        else:
            supernets.reverse()

        # Enumerate all unique networks and prefixes
        network_addresses = {unicode(s.network) for s in supernets}
        prefix_lengths = {s.prefixlen for s in supernets}
        del supernets  # Free the memory because DevOps.

        # Prepare the queryset filter
        lookup_kwargs = {
            'network_address__in': network_addresses,
            'prefix_length__in': prefix_lengths,
            'ip_version': ip_version,
            'broadcast_address__gte': broadcast_address,
        }
        if site is not None:
            lookup_kwargs['site'] = site

        # Search for possible ancestors by network/prefix, returning them in
        # reverse order, so that we can choose the first one.
        possible_ancestors = Network.objects.filter(
            **lookup_kwargs
        ).order_by('-prefix_length')

        # If we've got any matches, the first one is our closest parent.
        try:
            return possible_ancestors[0]
        except IndexError:
            raise Network.DoesNotExist(
                'Network matching query does not exist.'
            )

    def reserved(self):
        return Network.objects.filter(state=Network.RESERVED)


class Network(Resource):
    """Represents a subnet or IP address."""
    ALLOCATED = 'allocated'
    ASSIGNED = 'assigned'
    ORPHANED = 'orphaned'
    RESERVED = 'reserved'

    STATE_CHOICES = (
        (ALLOCATED, ALLOCATED.title()),
        (ASSIGNED, ASSIGNED.title()),
        (ORPHANED, ORPHANED.title()),
        (RESERVED, RESERVED.title()),
    )
    BUSY_STATES = [ASSIGNED, RESERVED]

    network_address = fields.BinaryIPAddressField(
        max_length=16, null=False, db_index=True,
        verbose_name='Network Address',
        help_text=(
            'The network address for the Network. The network address and '
            'the prefix length together uniquely define a network.'
        )
    )
    broadcast_address = fields.BinaryIPAddressField(
        max_length=16, null=False, db_index=True,
        help_text='The broadcast address for the Network. (Internal use only)'
    )
    prefix_length = models.IntegerField(
        null=False, db_index=True, verbose_name='Prefix Length',
        help_text='Length of the Network prefix, in bits.'
    )
    ip_version = models.CharField(
        max_length=1, null=False, db_index=True,
        choices=IP_VERSION_CHOICES
    )
    is_ip = models.BooleanField(
        null=False, default=False, db_index=True,
        help_text='Whether the Network is a host address or not.'
    )
    site = models.ForeignKey(
        Site, db_index=True, related_name='networks', on_delete=models.PROTECT,
        verbose_name='Site',
        help_text='Unique ID of the Site this Network is under.'
    )
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children', default=None,
        db_index=True, on_delete=models.PROTECT,
        help_text='The parent Network of the Network.'
    )
    state = models.CharField(
        max_length=20, null=False, db_index=True,
        choices=STATE_CHOICES, default=ALLOCATED,
        help_text='The allocation state of the Network.'
    )

    # Implements .objects.get_by_address() and .get_closest_parent()
    objects = NetworkManager()

    def __init__(self, *args, **kwargs):
        self._cidr = kwargs.pop('cidr', None)
        super(Network, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.cidr

    class Meta:
        unique_together = (
            'site', 'ip_version', 'network_address', 'prefix_length'
        )
        index_together = unique_together

    def supernets(self, direct=False, discover_mode=False, for_update=False):
        query = Network.objects.all()

        if self.parent is None and not discover_mode:
            return query.none()

        if discover_mode and direct:
            raise exc.ValidationError(
                'Direct is incompatible with discover_mode.'
            )

        if for_update:
            query = query.select_for_update()

        if direct:
            return query.filter(id=self.parent.id)

        return query.filter(
            site=self.site,
            is_ip=False,
            ip_version=self.ip_version,
            prefix_length__lt=self.prefix_length,
            network_address__lte=self.network_address,
            broadcast_address__gte=self.broadcast_address
        )

    def subnets(self, include_networks=True, include_ips=True, direct=False,
                for_update=False):
        query = Network.objects.all()

        if not any([include_networks, include_ips]) or self.is_ip:
            return query.none()

        if for_update:
            query = query.select_for_update()

        if not all([include_networks, include_ips]):
            if include_networks:
                query = query.filter(is_ip=False)
            if include_ips:
                query = query.filter(is_ip=True)

        if direct:
            return query.filter(parent__id=self.id)

        return query.filter(
            site=self.site,
            ip_version=self.ip_version,
            prefix_length__gt=self.prefix_length,
            network_address__gte=self.network_address,
            broadcast_address__lte=self.broadcast_address
        )

    # FIXME(jathan): This entire implementation needs to be revisited. It feels
    # as if it's too complicated. It may not be, but it feels like it is.
    def get_next_network(self, prefix_length, num=None, as_objects=True):
        """
        Return a list of the next available networks.

        If no networks are available, an empty list will be returned.

        :param prefix_length:
            The prefix length of networks

        :param num:
            The number of networks desired

        :param as_objects:
            Whether to return IPNetwork objects or strings

        :returns:
            list(IPNetwork)
        """
        # If we're reserved, automatically ZILCH!!
        # TODO(jathan): Should we raise an error instead?
        if self.state == Network.RESERVED:
            return []

        try:
            prefix_length = int(prefix_length)
        except (TypeError, ValueError) as err:
            raise exc.ValidationError({'prefix_length': err.message})

        if prefix_length < self.prefix_length:
            raise exc.ValidationError({
                'prefix_length': 'New prefix must be longer than %r' %
                self.prefix_length
            })

        # Default to 1.
        if num is None or num < 1:
            num = 1

        try:
            num = int(num)
        except ValueError as err:
            raise exc.ValidationError({'num': err.message})

        cidr = self.ip_network

        # If this network is an interconnect network, generate the hosts as
        # network objects, otherwise just subnet based on the prefix_length.
        # This is so that .0 and .1 could be allocated from a /31, for example.
        if cidr.prefixlen in settings.NETWORK_INTERCONNECT_PREFIXES:
            log.debug('CIDR %s is an interconnect!', cidr)
            subnets = (ipaddress.ip_network(ip) for ip in cidr)
        else:
            log.debug('cidr %s is NOT an interconnect!', cidr)
            subnets = cidr.subnets(new_prefix=prefix_length)

        # Exclude children that are in busy states.
        children = self.get_descendents()

        # FIXME(jathan): This can potentially be very slow if the gap between
        # parent and child networks is large, say, on the order of /8.
        # Something to keep in mind if it comes up in practical application,
        # especially with IPv6 networks, which is still not heavily tested.
        wanted = []  # Subnets we want.
        dirty = []   # Dirty subnets (have children)
        children_seen = []  # For child networks we've already processed.

        # Keep iterating until we've found the number of networks we want.
        while len(wanted) < num:
            try:
                next_subnet = next(subnets)
            except ValueError as err:
                raise exc.ValidationError({'prefix_length': err.message})
            except StopIteration:
                break

            # We can't allocate ourself.
            if next_subnet == cidr:
                continue

            # Never return 1st/last addresses if prefix is for an address,
            # unless it's an interconnect (aka point-to-point).
            # FIXME(jathan): Revisit why we made this decision. It seems
            # arbitrary.
            if cidr.prefixlen in settings.NETWORK_INTERCONNECT_PREFIXES:
                pass
            elif (next_subnet.prefixlen in settings.HOST_PREFIXES and
                    (next_subnet.network_address == cidr.network_address or
                        next_subnet.broadcast_address ==
                        cidr.broadcast_address)):
                continue

            log.debug('>> NEXT_SUBNET: %s', next_subnet)

            # Iterate the children and if we make it to the end, we've found a
            # keeper!
            for child in children:
                # This child is busy; mark it as seen.
                if child.state in self.BUSY_STATES:
                    children_seen.append(child.ip_network)
                    continue

                # Network is already wanted; skip it!
                if next_subnet in wanted:
                    log.debug('Network %s already wanted; skipping',
                              next_subnet)
                    break

                # This child has already been seen; skip it!
                if child.ip_network in children_seen:
                    continue

                # This network is already in use/allocated; skip it!
                # TODO(jathan): Decide if we want 'allocated' to also be a busy
                # state for the purpose of allocation? Yes, that's confusing,
                # but why not just treat this as a busy state? What about
                # orphaned state?
                if child.ip_network.overlaps(next_subnet):
                    log.debug('Child %s network overlaps w/ next_subnet %s',
                              child.ip_network, next_subnet)
                    children_seen.append(child.ip_network)
                    continue

            # We *might* want this subnet. But make sure it's clean first.
            else:
                # Skip dirty subnets.
                if next_subnet in dirty:
                    continue

                # Check all the children we've seen; if next_subnet contains
                # it, mark it as dirty.
                for child in children_seen:
                    if child.subnet_of(next_subnet):
                        log.debug(
                            '>> NEXT_SUBNET %s is DIRTY. Contains: %s',
                            next_subnet, child
                        )
                        dirty.append(next_subnet)
                        break

                # If we haven't seen it and it's not dirty, we want it!!
                subnet_wanted = all([
                    next_subnet not in children_seen,
                    next_subnet not in dirty
                ])
                if subnet_wanted:
                    log.info('>> NEXT_SUBNET %s is now wanted!', next_subnet)
                    wanted.append(next_subnet)

        log.info('>> WANTED = %s', wanted)

        return wanted if as_objects else [unicode(w) for w in wanted]

    def get_next_address(self, num=None, as_objects=True):
        """
        Return a list of the next available addresses.

        If no addresses are available, an empty list will be returned.

        :param num:
            The number of addresses desired

        :param as_objects:
            Whether to return IPNetwork objects or strings
        """
        prefix_map = {'4': 32, '6': 128}  # Map ip_version => prefix_length
        prefix_length = prefix_map.get(self.ip_version)

        return self.get_next_network(
            prefix_length=prefix_length, num=num, as_objects=as_objects
        )

    def is_child_node(self):
        """
        Returns whether I am a child node.
        """
        return self.parent is not None

    def is_leaf_node(self):
        """
        Returns whether I am leaf node (no children).
        """
        return not self.children.exists()

    def is_root_node(self):
        """
        Returns whether I am a root node (no parent).
        """
        return self.parent is None

    def get_ancestors(self, ascending=False):
        """Return my ancestors."""
        query = self.supernets().order_by('network_address', 'prefix_length')
        if ascending:
            query = query.reverse()
        return query

    def get_children(self):
        """Return my immediate children."""
        return self.subnets(include_ips=True, direct=True).order_by(
            'network_address', 'prefix_length'
        )

    def get_descendents(self):
        """Return all of my children!"""
        return self.subnets(include_ips=True).order_by(
            'network_address', 'prefix_length'
        )

    def get_root(self):
        """
        Returns the root node (the parent of all of my ancestors).
        """
        ancestors = self.get_ancestors()
        return ancestors.first()

    def get_siblings(self, include_self=False):
        """
        Return my siblings. Root nodes are siblings to other root nodes.
        """
        query = Network.objects.filter(
            parent=self.parent, site=self.site
        ).order_by('network_address', 'prefix_length')
        if not include_self:
            query = query.exclude(id=self.id)

        return query

    def get_utilization(self):
        return stats.get_network_utilization(self)

    def set_reserved(self, commit=True):
        self.state = self.RESERVED
        if commit:
            self.save()

    def set_assigned(self, commit=True):
        self.state = self.ASSIGNED
        if commit:
            self.save()

    def set_orphaned(self, commit=True):
        self.state = self.ORPHANED
        if commit:
            self.save()

    @property
    def cidr(self):
        return u'%s/%s' % (self.network_address, self.prefix_length)

    @property
    def ip_network(self):
        return ipaddress.ip_network(self.cidr)

    def reparent_subnets(self):
        """
        Determine list of child nodes and set the parent to self.
        """
        query = Network.objects.select_for_update().filter(
            ~models.Q(id=self.id),  # Don't include yourself...
            parent_id=self.parent_id,
            prefix_length__gt=self.prefix_length,
            ip_version=self.ip_version,
            network_address__gte=self.network_address,
            broadcast_address__lte=self.broadcast_address
        )

        query.update(parent=self)

    def clean_state(self, value):
        """Enforce that state is one of the valid states."""
        value = value.lower()
        if value not in [s[0] for s in self.STATE_CHOICES]:
            raise exc.ValidationError({
                'state': 'Invalid state: %r' % value
            })

        return value

    def clean_fields(self, exclude=None):
        """This will enforce correct values on fields."""
        cidr = self._cidr
        if cidr is None:
            if self.network_address and self.prefix_length:
                cidr = u'%s/%s' % (self.network_address, self.prefix_length)

        if not cidr:
            msg = "Invalid CIDR: {}. Must be IPv4/IPv6 notation.".format(cidr)
            raise exc.ValidationError(msg)

        # Determine network properties
        network = cidr  # In-case we're not a unicode string.

        # Convert to unicode in case it's bytes.
        if isinstance(cidr, basestring):
            cidr = unicode(cidr)

        # Convert a unicode string to an IPNetwork.
        if isinstance(cidr, unicode):
            try:
                network = ipaddress.ip_network(cidr)
            except ValueError as err:
                raise exc.ValidationError({
                    'cidr': err.message
                })

        if network.network_address == network.broadcast_address:
            self.is_ip = True

        self.ip_version = str(network.version)
        self.network_address = unicode(network.network_address)
        self.broadcast_address = unicode(network.broadcast_address)
        self.prefix_length = network.prefixlen
        self.state = self.clean_state(self.state)

    def save(self, *args, **kwargs):
        """This is stuff we want to happen upon save."""
        self.full_clean()  # First validate fields are correct

        for_update = kwargs.pop('for_update', False)

        # Calculate our supernets and determine if we require a parent.
        supernets = self.supernets(discover_mode=True, for_update=for_update)
        if supernets:
            parent = max(supernets, key=attrgetter('prefix_length'))
            self.parent = parent

        if self.parent is None and self.is_ip:
            raise exc.ValidationError('IP Address needs base network.')

        # Save, so we get an ID, and register our parent.
        super(Network, self).save(*args, **kwargs)

        # If we're not an IP, determine our subnets and reparent them.
        if not self.is_ip:
            self.reparent_subnets()

    def to_dict(self):
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'site_id': self.site_id,
            'is_ip': self.is_ip,
            'ip_version': self.ip_version,
            'network_address': self.network_address,
            'prefix_length': self.prefix_length,
            'state': self.state,
            'attributes': self.get_attributes(),
        }


class Interface(Resource):
    """A network interface."""
    # if_name
    # SNMP: ifName
    # if_description
    # SNMP: ifDescr
    name = models.CharField(
        max_length=255, null=False, db_index=True,
        help_text='The name of the interface as it appears on the Device.'
    )

    # if_addr
    # m2m Network object /32 or /128
    addresses = models.ManyToManyField(
        Network, db_index=True, related_name='addresses', through='Assignment',
        help_text='Network addresses assigned to this Interface'
    )

    # if_alias - String of interface description
    # SNMP: ifAlias
    description = models.CharField(
        max_length=255, default='', blank=True, null=False,
        help_text='A brief yet helpful description.'
    )

    # server_id
    device = models.ForeignKey(
        Device, db_index=True, related_name='interfaces', null=False,
        verbose_name='Device', help_text='Unique ID of the connected Device.'
    )

    # if_type - Integer of interface type id (Ethernet, LAG, etc.)
    # SNMP: ifType
    type = models.IntegerField(
        'Interface Type', choices=settings.INTERFACE_TYPE_CHOICES,
        default=settings.INTERFACE_DEFAULT_TYPE,
        null=False, db_index=True,
        help_text="If not provided, defaults to 'ethernet'."
    )

    # if_physical_address - Integer of hex MAC address
    # SNMP: ifPhysAddress
    mac_address = fields.MACAddressField(
        'MAC Address', blank=True, db_index=True, null=True,
        default=int(settings.INTERFACE_DEFAULT_MAC), help_text=(
            'If not provided, defaults to %s.' %
            settings.INTERFACE_DEFAULT_MAC
        )
    )

    # if_speed - Should not be used. Caps at 4.3GB (2^32)
    # SNMP: ifSpeed

    # if_high_speed - Integer of Mbps of interface (e.g. 20000 for 20 Gbps)
    # SNMP: ifHighSpeed
    speed = models.IntegerField(
        blank=True, db_index=True, default=settings.INTERFACE_DEFAULT_SPEED,
        help_text=(
            'Integer of Mbps of interface (e.g. 20000 for 20 Gbps). If not '
            'provided, defaults to %d.' % settings.INTERFACE_DEFAULT_SPEED
        )
    )

    parent = fields.ChainedForeignKey(
        'nsot.Interface', blank=True, null=True, related_name='children',
        default=None, db_index=True, on_delete=models.PROTECT,
        chained_field='device', chained_model_field='device',
        verbose_name='Parent', help_text='Unique ID of the parent Interface.',
    )

    # We are currently inferring the site_id from the parent Device in the
    # .save() method. We don't want to even care about the site_id , but it
    # simplifies managing them this way.
    site = models.ForeignKey(
        Site, db_index=True, related_name='interfaces',
        on_delete=models.PROTECT,
        help_text='Unique ID of the Site this Interface is under.'
    )

    # Where list of assigned addresses is cached.
    _addresses_cache = fields.JSONField(null=False, blank=True, default=[])

    # Where list of attached networks is cached.
    _networks_cache = fields.JSONField(null=False, blank=True, default=[])

    def __init__(self, *args, **kwargs):
        self._set_addresses = kwargs.pop('addresses', None)
        super(Interface, self).__init__(*args, **kwargs)

    ##########################################
    # THESE WILL BE IMPLEMENTED AS ATTRIBUTES
    ##########################################

    # Using the "indexing strategy" concept, which I think will be pluggable.
    # if_index - Integer of SNMP interface index on device
    # SNMP: ifIndex
    # snmp_index

    # if_parent_index
    # snmp_parent_index

    # LLDP adjacencies
    # These should be deployed as attributes.
    # lldp_remote_port_desc
    # lldp_remote_system_name

    def __unicode__(self):
        return u'device=%s, name=%s' % (self.device.id, self.name)

    class Meta:
        unique_together = ('device', 'name')
        index_together = unique_together

    @property
    def networks(self):
        """Return all the parent Networks for my addresses."""
        return Network.objects.filter(
            id__in=self.addresses.values_list('parent')
        ).distinct()

    def _purge_addresses(self):
        """Delete all of my addresses (and therefore assignments)."""
        self.addresses.all().delete()
        self.clean_addresses()  # Always re-cache after we purge addresses..

    def _purge_assignments(self):
        """Delete all of my assignments, leaving the Network objects intact."""
        self.assignments.all().delete()
        self.clean_addresses()  # Always re-cache after we purge assignments.

    def assign_address(self, cidr):
        """
        Assign an address to this interface.

        Must have prefix of /32 (IPv4) or /128 (IPv6).

        :param cidr:
            IPv4/v6 CIDR host address or Network object
        """
        cidr = validators.validate_host_address(cidr)
        try:
            address = Network.objects.get_by_address(cidr, site=self.site)
        except Network.DoesNotExist:
            address = Network.objects.create(cidr=cidr, site=self.site)
            created = True
        else:
            created = False

        # If we've created a Network, and assignment fails, then we need to
        # make sure that we delete that Network.
        try:
            return Assignment.objects.create(interface=self, address=address)
        except exc.ValidationError:
            # Clean up the address if we created one..
            if created:
                address.delete()
            raise

    def set_addresses(self, addresses, overwrite=False, partial=False):
        """
        Explicitly assign a list of addresses to this Interface.

        :param addresses:
            A list of CIDRs

        :param overwrite:
            Whether to purge existing assignments before assigning.

        :param partial:
            Whether this is a partial update.
        """
        log.debug(
            'Interface.set_addresses() addresses = %r', addresses
        )

        # If no addresses and it's a partial update, NOOP.
        if addresses is None and partial:
            return None

        if not isinstance(addresses, list):
            raise exc.ValidationError({
                'addresses': 'Expected list but received {}'.format(
                    type(addresses)
                )
            })

        if overwrite:
            self._purge_assignments()

        # Keep track of addresses that are already assigned so we don't try to
        # assign them again (which would result in an error).
        existing_addresses = self.get_addresses()

        inserts = []
        for cidr in addresses:
            # Don't assign an address that already exists.
            if cidr in existing_addresses:
                continue

            address = validators.validate_cidr(cidr)
            inserts.append(str(address))

        for insert in inserts:
            self.assign_address(insert)

        self.clean_addresses()

    def get_assignments(self):
        """Return a list of informatoin about my assigned addresses."""
        return [a.to_dict() for a in self.assignments.all()]

    def get_addresses(self):
        """Return a list of assigned addresses."""
        return self._addresses_cache

    def get_networks(self):
        """Return a list of attached Networks."""
        return self._networks_cache

    def get_mac_address(self):
        """Return a serializable representation of mac_address."""
        if self.mac_address is None:
            return
        return str(self.mac_address)

    def clean_addresses(self):
        """Make sure that addresses/networks are saved as JSON."""
        addresses = [a.cidr for a in self.addresses.iterator()]
        self._addresses_cache = addresses

        networks = [n.cidr for n in self.networks.iterator()]
        self._networks_cache = networks

    def clean_name(self, value):
        """Enforce name."""
        return validators.validate_name(value)

    def clean_site(self, value):
        """Always enforce that site is set."""
        if value is None:
            try:
                return self.device.site_id
            except Device.DoesNotExist:
                return Device.objects.get(id=self.device_id).site_id

        return value

    def clean_speed(self, value):
        """Enforce valid speed."""
        # We don't want floats because they can be misleading, also Django's
        # IntegerField will cast a float to an int, which loses precision.
        # TODO (jathan): Reconsider this as a float? Maybe? We might not care
        # about things like 1.544 (T1) anymore...
        if isinstance(value, float):
            raise exc.ValidationError({
                'speed': 'Speed must be an integer.'
            })

        try:
            value = int(value)
        except ValueError:
            raise exc.ValidationError({
                'speed': 'Invalid speed: %r' % value
            })
        else:
            return value

    def clean_type(self, value):
        """Enforce valid type."""
        if value not in INTERFACE_TYPES:
            raise exc.ValidationError({
                'type': 'Invalid type: %r' % value
            })

        return value

    def clean_mac_address(self, value):
        """Enforce valid mac_address."""
        return validators.validate_mac_address(value)

    def clean_fields(self, exclude=None):
        self.site_id = self.clean_site(self.site_id)
        self.name = self.clean_name(self.name)
        self.type = self.clean_type(self.type)
        self.speed = self.clean_speed(self.speed)
        self.mac_address = self.clean_mac_address(self.mac_address)

    def save(self, *args, **kwargs):
        # We don't want to validate unique because we want the IntegrityError
        # to fall through so we can catch it an raise a 409 CONFLICT.
        self.full_clean(validate_unique=False)
        super(Interface, self).save(*args, **kwargs)

        # This is so that we can set the addresses on create/update, but if
        # the object is new, make sure that it doesn't persist if addresses
        # fail.
        if self._set_addresses is not None:
            try:
                # And set the attributes (if any)
                self.set_addresses(self._set_addresses)
            except exc.ValidationError:
                # If addresses fail validation, and I'm a new object, delete
                # myself and re-raise the error.
                if self._is_new:  # This is set by Resource.save()
                    self.delete()
                raise

    def to_dict(self):
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'device': self.device_id,
            'description': self.description,
            'addresses': self.get_addresses(),
            'networks': self.get_networks(),
            'mac_address': self.get_mac_address(),
            'speed': self.speed,
            'type': self.type,
            'attributes': self.get_attributes(),
        }


class Assignment(models.Model):
    """
    DB object for assignment of addresses to interfaces (on devices).

    This is used to enforce constraints at the relationship level for addition
    of new address assignments.
    """
    address = models.ForeignKey(
        Network, related_name='assignments', db_index=True,
        help_text='Network to which this assignment is bound.'
    )
    interface = models.ForeignKey(
        Interface, related_name='assignments', db_index=True,
        help_text='Interface to which this assignment is bound.'
    )
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'interface=%s, address=%s' % (self.interface, self.address)

    class Meta:
        unique_together = ('address', 'interface')
        index_together = unique_together

    def clean_address(self, value):
        """Enforce that new addresses can only be host addresses."""
        addr = validators.validate_host_address(value)

        # Enforce uniqueness upon assignment.
        existing = Assignment.objects.filter(address=addr)
        if existing.filter(interface__device=self.interface.device).exists():
            raise exc.ValidationError({
                'address': 'Address already assigned to this Device.'
            })

        return value

    def clean_fields(self, exclude=None):
        self.clean_address(self.address)
        self.address.set_assigned()

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Assignment, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'device': self.interface.device.id,
            'hostname': self.interface.device.hostname,
            'interface': self.interface.id,
            'interface_name': self.interface.name,
            'address': self.address.cidr,
        }


class Attribute(models.Model):
    """Represents a flexible attribute for Resource objects."""
    # This is purposely not unique as there is a compound index with site_id.
    name = models.CharField(
        max_length=64, null=False, db_index=True,
        help_text='The name of the Attribute.'
    )
    description = models.CharField(
        max_length=255, default='', blank=True, null=False,
        help_text='A helpful description of the Attribute.'
    )

    # The resource must contain a key and value
    required = models.BooleanField(
        default=False, null=False,
        help_text='Whether the Attribute should be required.'
    )

    # In UIs this attribute will be displayed by default. Required implies
    # display.
    display = models.BooleanField(
        default=False, null=False,
        help_text=(
            'Whether the Attribute should be be displayed by default in '
            'UIs. If required is set, this is also set.'
        )
    )

    # Attribute values are expected as lists of strings.
    multi = models.BooleanField(
        default=False, null=False,
        help_text='Whether the Attribute should be treated as a list type.'
    )

    constraints = fields.JSONField(
        'Constraints', null=False, blank=True,
        help_text='Dictionary of Attribute constraints.'
    )

    site = models.ForeignKey(
        Site, db_index=True, related_name='attributes',
        on_delete=models.PROTECT, verbose_name='Site',
        help_text='Unique ID of the Site this Attribute is under.'
    )

    resource_name = models.CharField(
        'Resource Name', max_length=20, null=False, db_index=True,
        choices=RESOURCE_CHOICES,
        help_text='The name of the Resource to which this Attribute is bound.'
    )

    def __unicode__(self):
        return u'%s %s (site_id: %s)' % (
            self.resource_name, self.name, self.site_id
        )

    class Meta:
        unique_together = ('site', 'resource_name', 'name')
        index_together = unique_together

    @classmethod
    def all_by_name(cls, resource_name=None, site=None):
        if resource_name is None:
            raise SyntaxError('You must provided a resource_name.')
        if site is None:
            raise SyntaxError('You must provided a site.')

        query = cls.objects.filter(resource_name=resource_name, site=site)

        return {
            attribute.name: attribute
            for attribute in query.all()
        }

    def clean_constraints(self, value):
        """Enforce formatting of constraints."""
        if not isinstance(value, dict):
            raise exc.ValidationError({
                'constraints': 'Expected dictionary but received {}.'.format(
                    type(value))
                })

        constraints = {
            'allow_empty': value.get('allow_empty', False),
            'pattern': value.get('pattern', ''),
            'valid_values': value.get('valid_values', []),
        }

        if not isinstance(constraints['allow_empty'], bool):
            raise exc.ValidationError({
                'constraints': 'allow_empty expected type bool.'
            })

        if not isinstance(constraints['pattern'], basestring):
            raise exc.ValidationError({
                'constraints': 'pattern expected type string.'
            })

        if not isinstance(constraints['valid_values'], list):
            raise exc.ValidationError({
                'constraints': 'valid_values expected type list.'
            })

        return constraints

    def clean_display(self, value):
        if self.required:
            return True
        return value

    def clean_resource_name(self, value):
        if value not in VALID_ATTRIBUTE_RESOURCES:
            raise exc.ValidationError({
                'resource_name': 'Invalid resource name: %r.' % value
            })
        return value

    def clean_name(self, value):
        value = validators.validate_name(value)

        if not settings.ATTRIBUTE_NAME.match(value):
            raise exc.ValidationError({
                'name': 'Invalid name: %r.' % value
            })

        return value or False

    def clean_fields(self, exclude=None):
        self.constraints = self.clean_constraints(self.constraints)
        self.display = self.clean_display(self.display)
        self.resource_name = self.clean_resource_name(self.resource_name)
        self.name = self.clean_name(self.name)

    def _validate_single_value(self, value, constraints=None):
        if not isinstance(value, basestring):
            raise exc.ValidationError({
                'value': 'Attribute values must be a string type'
            })

        if constraints is None:
            constraints = self.constraints

        allow_empty = constraints.get('allow_empty', False)
        if not allow_empty and not value:
            raise exc.ValidationError({
                'constraints': "Attribute {} doesn't allow empty values"
                .format(self.name)
            })

        pattern = constraints.get('pattern')
        if pattern and not re.match(pattern, value):
            raise exc.ValidationError({
                'pattern': "Attribute value {} for {} didn't match pattern: {}"
                .format(value, self.name, pattern)
            })

        valid_values = set(constraints.get('valid_values', []))
        if valid_values and value not in valid_values:
            raise exc.ValidationError(
                'Attribute value {} for {} not a valid value: {}'
                .format(value, self.name, ', '.join(valid_values))
            )

        return {
            'attribute_id': self.id,
            'value': value,
        }

    def validate_value(self, value):
        if self.multi:
            if not isinstance(value, list):
                raise exc.ValidationError({
                    'multi': 'Attribute values must be a list type'
                })
        else:
            value = [value]

        inserts = []
        # This does a deserialization so save the result
        constraints = self.constraints
        for val in value:
            inserts.append(self._validate_single_value(val, constraints))

        return inserts

    def save(self, *args, **kwargs):
        """Always enforce constraints."""
        self.full_clean()
        super(Attribute, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'site_id': self.site_id,
            'description': self.description,
            'name': self.name,
            'resource_name': self.resource_name,
            'required': self.required,
            'display': self.display,
            'multi': self.multi,
            'constraints': self.constraints,
        }


class Value(models.Model):
    """Represents a value for an attribute attached to a Resource."""
    attribute = models.ForeignKey(
        Attribute, related_name='values', db_index=True,
        on_delete=models.PROTECT,
        help_text='The Attribute to which this Value is assigned.'
    )
    value = models.CharField(
        max_length=255, null=False, blank=True, db_index=True,
        help_text='The Attribute value.'
    )
    resource_id = models.IntegerField(
        'Resource ID', null=False,
        help_text='The unique ID of the Resource to which the Value is bound.',
    )
    resource_name = models.CharField(
        'Resource Type', max_length=20, null=False, db_index=True,
        choices=CHANGE_RESOURCE_CHOICES,
        help_text='The name of the Resource type to which the Value is bound.',
    )
    name = models.CharField(
        'Name', max_length=64, null=False, blank=True,
        help_text=(
            'The name of the Attribute to which the Value is bound. '
            '(Internal use only)'
        )
    )

    # We are currently inferring the site_id from the parent Attribute in
    # .save() method. We don't want to even care about the site_id, but it
    # simplifies managing them this way.
    site = models.ForeignKey(
        Site, db_index=True, related_name='values',
        on_delete=models.PROTECT, verbose_name='Site',
        help_text='Unique ID of the Site this Value is under.'
    )

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.pop('obj', None)
        super(Value, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u'%s:%s %s=%s' % (self.resource_name, self.resource_id,
                                 self.name, self.value)

    class Meta:
        unique_together = ('name', 'value', 'resource_name', 'resource_id')

        # This is most commonly looked up
        index_together = [
            ('name', 'value', 'resource_name'),
            ('resource_name', 'resource_id'),
        ]

    def clean_resource_name(self, value):
        if value not in VALID_CHANGE_RESOURCES:
            raise exc.ValidationError('Invalid resource name: %r.' % value)
        return value

    def clean_name(self, attr):
        return attr.name

    def clean_site(self, value):
        """Always enforce that site is set."""
        if value is None:
            try:
                return self.attribute.site_id
            except Attribute.DoesNotExist:
                return Attribute.objects.get(id=self.attribute_id).site_id

        return value

    def clean_fields(self, exclude=None):
        obj = self._obj
        if obj is None:
            return None

        self.site_id = self.clean_site(self.site_id)
        self.resource_name = self.clean_resource_name(obj.__class__.__name__)
        self.resource_id = obj.id
        self.name = self.clean_name(self.attribute)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Value, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'attribute': self.attribute_id,
            'resource_name': self.resource_name,
            'resource_id': self.resource_id,
        }


class Change(models.Model):
    """Record of all changes in NSoT."""
    site = models.ForeignKey(
        Site, db_index=True, related_name='changes', verbose_name='Site',
        help_text='Unique ID of the Site this Change is under.'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='changes', db_index=True,
        help_text='The User that initiated this Change.'
    )
    change_at = models.DateTimeField(
        auto_now_add=True, null=False,
        help_text='The timestamp of this Change.'
    )
    event = models.CharField(
        max_length=10, null=False, choices=EVENT_CHOICES,
        help_text='The type of event this Change represents.'
    )
    resource_id = models.IntegerField(
        'Resource ID', null=False,
        help_text='The unique ID of the Resource for this Change.'
    )
    resource_name = models.CharField(
        'Resource Type', max_length=20, null=False, db_index=True,
        choices=CHANGE_RESOURCE_CHOICES,
        help_text='The name of the Resource for this Change.'
    )
    _resource = fields.JSONField(
        'Resource', null=False, blank=True,
        help_text='Local cache of the changed Resource. (Internal use only)'
    )

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.pop('obj', None)
        super(Change, self).__init__(*args, **kwargs)

    class Meta:
        get_latest_by = 'change_at'

    def __unicode__(self):
        return u'%s %s(%s)' % (self.event, self.resource_name,
                               self.resource_id)

    @property
    def resource(self):
        return self._resource

    def get_change_at(self):
        return timegm(self.change_at.timetuple())
    get_change_at.short_description = 'Change At'

    @classmethod
    def get_serializer_for_resource(cls, resource_name):
        from .api import serializers
        serializer_class = resource_name + 'Serializer'
        return getattr(serializers, serializer_class)

    def clean_event(self, value):
        if value not in CHANGE_EVENTS:
            raise exc.ValidationError('Invalid change event: %r.' % value)
        return value

    def clean_resource_name(self, value):
        if value not in VALID_CHANGE_RESOURCES:
            raise exc.ValidationError('Invalid resource name: %r.' % value)
        return value

    def clean_fields(self, exclude=None):
        """This will populate the change fields from the incoming object."""
        obj = self._obj
        if obj is None:
            return None

        self.event = self.clean_event(self.event)
        self.resource_name = self.clean_resource_name(obj.__class__.__name__)
        self.resource_id = obj.id

        # Site doesn't have an id to itself, so if obj is a Site, use it.
        self.site = obj if isinstance(obj, Site) else obj.site

        serializer_class = self.get_serializer_for_resource(self.resource_name)
        serializer = serializer_class(obj)
        self._resource = serializer.data

    def save(self, *args, **kwargs):
        self.full_clean()  # First validate fields are correct
        super(Change, self).save(*args, **kwargs)

    def to_dict(self):
        resource = None
        if self.resource is not None:
            resource = self.resource

        return {
            'id': self.id,
            'site': self.site.to_dict(),
            'user': self.user.to_dict(),
            'change_at': timegm(self.change_at.timetuple()),
            'event': self.event,
            'resource_name': self.resource_name,
            'resource_id': self.resource_id,
            'resource': resource,
        }


# Signals
def delete_resource_values(sender, instance, **kwargs):
    """Delete values when a Resource object is deleted."""
    instance.attributes.delete()  # These are instances of Value


def change_api_updated_at(sender=None, instance=None, *args, **kwargs):
    """Anytime the API is updated, invalidate the cache."""
    djcache.set('api_updated_at_timestamp', timezone.now())


# Register signals
resource_subclasses = Resource.__subclasses__()
for model_class in resource_subclasses:
    # Value post_delete
    models.signals.post_delete.connect(
        delete_resource_values,
        sender=model_class,
        dispatch_uid='value_post_delete_' + model_class.__name__
    )


# Invalidate Interface cache on save/delete
models.signals.post_save.connect(
    change_api_updated_at, sender=Interface,
    dispatch_uid='invalidate_cache_post_save_interface'
)
models.signals.post_delete.connect(
    change_api_updated_at, sender=Interface,
    dispatch_uid='invalidate_cache_post_delete_interface'
)
