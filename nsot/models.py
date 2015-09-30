# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from calendar import timegm
from cryptography.fernet import (Fernet, InvalidToken)
from custom_user.models import AbstractEmailUser
from django.db import models
from django.db.models.query_utils import Q
from django.conf import settings
from django.core.exceptions import (ValidationError as DjangoValidationError,
                                    ObjectDoesNotExist)
from django.core.validators import EmailValidator
import ipaddress
import json
import logging
from operator import attrgetter
from polymorphic import PolymorphicModel, PolymorphicManager
from polymorphic.query import PolymorphicQuerySet
import re

from . import exc
from . import fields
from . import validators
from .util import generate_secret_key, parse_set_query


log = logging.getLogger(__name__)

# These are constants that becuase they are tied directly to the underlying
# objects are explicitly NOT USER CONFIGURABLE.
RESOURCE_BY_IDX = (
    'Site', 'Network', 'Attribute', 'Permission', 'Device', 'Interface'
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
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(default='', blank=True)

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
    secret_key = models.CharField(max_length=44, default=generate_secret_key)

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
        validator = EmailValidator()
        try:
            validator(value)
        except DjangoValidationError as err:
            raise exc.ValidationError({
                'email': err.message
            })
        return value

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


class ResourceSetTheoryQuerySet(PolymorphicQuerySet):
    """
    Set theory QuerySet for Resource objects to add ``.set_query()`` method.

    For example::

        >>> qs = Network.objects.filter(network_address=u'10.0.0.0')
        >>> qs.set_query('owner=jathan +metro=lax')
    """
    def set_query(self, query, site_id=None):
        objects = self
        if site_id is not None:
            objects = objects.filter(site=site_id)

        try:
            attributes = parse_set_query(query)
        except (ValueError, TypeError):
            attributes = []

        resource_name = self.model.__name__

        # Iterate a/v pairs and combine query results using MySQL-compatible
        # set operations w/ the ORM
        log.debug('QUERY [start]: objects = %r', objects)
        for action, name, value in attributes:
            params = dict(
                name=name, resource_name=resource_name
            )
            # Only include site_id if it's set
            if site_id is not None:
                params['site_id'] = site_id
            attr = Attribute.objects.get(
                **params
            )
            next_set = Q(
                attributes=Value.objects.filter(
                    attribute_id=attr.id, value=value
                ).values_list('id', flat=True)
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


class ResourceManager(PolymorphicManager):
    """
    Manager for Resource objects that adds a ``.set_query()`` method.

    For example::

        >>> Network.objects.set_query('owner=jathan +metro=lax'}
        [<Device: foo-bar1>]
    """
    queryset_class = ResourceSetTheoryQuerySet

    def set_query(self, query, site_id=None):
        try:
            return self.get_queryset().set_query(query, site_id)
        # If no matching objects are found, return an empty queryset.
        except ObjectDoesNotExist:
            return self.get_queryset().none()


class Resource(PolymorphicModel):
    """Base for heirarchial Resource objects that may have attributes."""
    _attributes = fields.JSONField(null=False, blank=True)

    def __init__(self, *args, **kwargs):
        self._set_attributes = kwargs.pop('attributes', None)
        super(Resource, self).__init__(*args, **kwargs)

    # Implement .objects.set_query()
    objects = ResourceManager()

    @property
    def _resource_name(self):
        return self._meta.model_name.title()

    def _purge_attribute_index(self):
        self.attributes.all().delete()

    def get_attributes(self):
        """Return the JSON-encoded attributes as a dict."""
        return self._attributes

    def set_attributes(self, attributes, valid_attributes=None):
        """Validate and store the attributes dict as a JSON-encoded string."""
        log.debug('Resource.set_attributes() attributes = %r',
                  attributes)
        if not isinstance(attributes, dict):
            raise exc.ValidationError(
                'Expected dictionary but received {}'.format(type(attributes))
            )

        if valid_attributes is None:
            valid_attributes = Attribute.all_by_name(
                self._resource_name, self.site
            )
        log.debug('Resource.set_attributes() valid_attributes = %r',
                  valid_attributes)

        missing_attributes = {
            attribute.name for attribute in valid_attributes.itervalues()
            if attribute.required and attribute.name not in attributes
        }
        log.debug('Resource.set_attributes() missing_attributes = %r',
                  missing_attributes)

        if missing_attributes:
            names = ', '.join(missing_attributes)
            raise exc.ValidationError(
                'Missing required attributes: {}'.format(names)
            )

        inserts = []
        for name, value in attributes.iteritems():
            if name not in valid_attributes:
                raise exc.ValidationError(
                    'Attribute name ({}) does not exist.'.format(name)
                )

            if not isinstance(name, basestring):
                raise exc.ValidationError(
                    'Attribute names must be a string type.'
                )

            attribute = valid_attributes[name]
            inserts.extend(attribute.validate_value(value))

        # Purge all of our previously existing attribute values and recreate
        # them anew. This isn't exactly efficient.
        self._purge_attribute_index()
        for insert in inserts:
            Value.objects.create(
                resource=self, attribute_id=insert['attribute_id'],
                value=insert['value']
            )

        self.clean_attributes()

    def clean_attributes(self):
        """Make sure that attributes are saved as JSON."""
        attrs = {}
        for a in self.attributes.all():
            if a.attribute.multi:
                if a.name not in attrs:
                    attrs[a.name] = []
                attrs[a.name].append(a.value)
            else:
                attrs[a.name] = a.value
        self._attributes = attrs
        return attrs

    def clean_fields(self, exclude=None):
        self._attributes = self.clean_attributes()

    def save(self, *args, **kwargs):
        self._is_new = self.id is None  # Check if this is a new object.
        # self.full_clean()
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
    hostname = models.CharField(max_length=255, null=False, db_index=True)
    site = models.ForeignKey(
        Site, db_index=True, related_name='devices', on_delete=models.PROTECT
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
    def get_by_address(self, cidr):
        """Lookup a Network object by ``cidr``."""
        cidr = validators.validate_cidr(cidr)
        address = Network.objects.get(
            network_address=cidr.network_address,
            prefix_length=cidr.prefixlen
        )
        return address


class Network(Resource):
    """Represents a subnet or ip address."""
    network_address = fields.BinaryIPAddressField(
        max_length=16, null=False, db_index=True
    )
    broadcast_address = fields.BinaryIPAddressField(
        max_length=16, null=False, db_index=True
    )
    prefix_length = models.IntegerField(null=False, db_index=True)
    ip_version = models.CharField(
        max_length=1, null=False, db_index=True,
        choices=IP_VERSION_CHOICES
    )
    is_ip = models.BooleanField(null=False, default=False, db_index=True)
    site = models.ForeignKey(
        Site, db_index=True, related_name='networks', on_delete=models.PROTECT
    )
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children', default=None,
        on_delete=models.PROTECT,
    )

    # Implements .objects.get_by_address()
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

    def subnets(self, include_networks=True, include_ips=False, direct=False,
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
        """
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
        subnets = cidr.subnets(new_prefix=prefix_length)
        children = self.get_children()

        # FIXME(jathan): This can potentially be very slow if the gap between
        # parent and child networks is large, say, on the order of /8.
        # Something to keep in mind if it comes up in practical application,
        # especially with IPv6 networks, which is still not heavily tested.
        wanted = []
        children_seen = []
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
            if cidr.prefixlen == settings.NETWORK_INTERCONNECT_PREFIXLEN:
                pass
            elif (next_subnet.prefixlen in settings.HOST_PREFIXES and
                    (next_subnet.network_address == cidr.network_address or
                        next_subnet.broadcast_address ==
                        cidr.broadcast_address)):
                continue

            # Iterate the children and if we make it to the end, we've found a
            # keeper!
            for child in children:
                # Network is already wanted; skip it!
                if next_subnet in wanted:
                    break

                # This child has already been seen; skip it!
                if child.ip_network in children_seen:
                    continue

                # This network is already in use/allocated; skip it!
                if child.ip_network.overlaps(next_subnet):
                    children_seen.append(child.ip_network)
                    continue
                else:
                    break

            # We want this one; keep it!!
            else:
                if next_subnet not in children_seen:
                    wanted.append(next_subnet)

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
        help_text='The name of the interface as it appears on the device.'
    )

    # if_addr
    # Should this instead be a 1-to-1 to a Network object /32 or /128?
    # address = fields.BinaryIPAddressField(max_length=16, db_index=True)
    addresses = models.ManyToManyField(
        Network, db_index=True, related_name='addresses', through='Assignment'
    )

    # if_alias - String of interface description
    # SNMP: ifAlias
    description = models.CharField(
        max_length=255, default='', blank=True, null=False
    )

    # server_id
    device = models.ForeignKey(
        Device, db_index=True, related_name='interfaces', null=False
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

    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children', default=None,
        on_delete=models.PROTECT,
    )

    # We are currently inferring the site_id from the parent Device both in the
    # serializers for the API and in the .save() method to be doubly sure. We
    # don't want to even care about the site_id for interfaces, but it
    # simplifies managing them this way.
    site = models.ForeignKey(
        Site, db_index=True, related_name='interfaces',
        on_delete=models.PROTECT
    )

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
        return Network.objects.filter(id=self.addresses.values_list('parent'))

    def _purge_addresses(self):
        """Delete all of my addresses (and therefore assignments)."""
        self.addresses.all().delete()

    def _purge_assignments(self):
        """Delete all of my assignments, leaving the Network objects intact."""
        self.assignments.all().delete()

    def assign_address(self, cidr):
        """
        Assign an address to this interface.

        Must have prefix of /32 (IPv4) or /128 (IPv6).

        :param cidr:
            IPv4/v6 CIDR host address or Network object
        """
        cidr = validators.validate_host_address(cidr)
        try:
            address = Network.objects.get_by_address(cidr)
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

    def set_addresses(self, addresses, overwrite=False):
        """
        Explicitly assign a list of addresses to this Interface.

        :param addresses:
            A list of CIDRs

        :param overwrite:
            Whether to purge existing assignments before assigning.
        """
        log.debug(
            'Interface.set_addresses() addresses = %r', addresses
        )

        if not isinstance(addresses, list):
            raise exc.ValidationError(
                'Expected list but received {}'.format(type(addresses))
            )

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

    def get_assignments(self):
        """Return a list of informatoin about my assigned addresses."""
        return [a.to_dict() for a in self.assignments.all()]

    def get_addresses(self):
        """Return a list of assigned addresses."""
        return [a.cidr for a in self.addresses.all()]

    def get_networks(self):
        """Return a list of attached Networks."""
        return [n.cidr for n in self.networks]

    def get_device_site(self):
        """Return the Site for my Device."""
        return Device.objects.get(id=self.device_id).site

    def clean_name(self, value):
        """Enforce name."""
        return validators.validate_name(value)

    def clean_site(self, value):
        """Always enforce that site is set."""
        if value is None:
            value = self.get_device_site().id  # Use Device's site_id.
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
        try:
            validators.validate_mac_address(value)
        except DjangoValidationError as err:
            raise exc.ValidationError({
                'mac_address': err.message
            })
        return value

    def full_clean(self, exclude=None):
        self.site_id = self.clean_site(self.site_id)
        self.name = self.clean_name(self.name)
        self.type = self.clean_type(self.type)
        self.speed = self.clean_speed(self.speed)
        self.mac_address = self.clean_mac_address(self.mac_address)

    def save(self, *args, **kwargs):
        self.full_clean()
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
            # 'site_id': self.site_id,  # We're relying on Device's site.
            'name': self.name,
            'device_id': self.device_id,
            'description': self.description,
            'addresses': self.get_addresses(),
            'networks': self.get_networks(),
            'mac_address': str(self.mac_address),
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
        Network, related_name='assignments', db_index=True
    )
    interface = models.ForeignKey(
        Interface, related_name='assignments', db_index=True
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Assignment, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'device': self.interface.device.id,
            'interface': self.interface.id,
            'address': self.address.cidr,
        }


def validate_name(value):
    if not value:
        raise exc.ValidationError("Name is a required field.")

    if not settings.ATTRIBUTE_NAME.match(value):
        raise exc.ValidationError("Invalid name.")

    return value or False


class Attribute(models.Model):
    """Represents a flexible attribute for Resource objects."""
    # This is purposely not unique as there is a compound index with site_id.
    name = models.CharField(max_length=64, null=False, db_index=True)
    description = models.CharField(
        max_length=255, default='', blank=True, null=False
    )

    # The resource must contain a key and value
    required = models.BooleanField(default=False, null=False)

    # In UIs this attribute will be displayed by default. Required implies
    # display.
    display = models.BooleanField(default=False, null=False)

    # Attribute values are expected as lists of strings.
    multi = models.BooleanField(default=False, null=False)

    constraints = fields.JSONField(null=False, blank=True)

    site = models.ForeignKey(
        Site, db_index=True, related_name='attributes',
        on_delete=models.PROTECT
    )

    resource_name = models.CharField(
        'Resource Name', max_length=20, null=False, db_index=True,
        choices=RESOURCE_CHOICES
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
        on_delete=models.PROTECT
    )
    value = models.CharField(
        max_length=255, null=False, blank=True,
        db_index=True
    )
    resource = models.ForeignKey(
        'Resource', related_name='attributes', db_index=True,
        blank=True
    )

    def __unicode__(self):
        return u'%r %s=%s' % (self.resource, self.name, self.value)

    class Meta:
        unique_together = ('attribute', 'value', 'resource')
        index_together = unique_together

    @property
    def name(self):
        return self.attribute.name

    @property
    def resource_name(self):
        return self.attribute.resource_name

    def clean_fields(self, exclude=None):
        log.debug('cleaning %s', self.name)
        # Make sure that the resource's type matches the resource name
        if self.resource_name != self.resource._resource_name:
            raise exc.ValidationError({
                'attribute': 'Invalid attribute type for this resource.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Value, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'attribute': self.attribute.to_dict(),
            'resource_name': self.resource_name,
            'resource': self.resource.to_dict(),
        }


class Change(models.Model):
    """Record of all changes in NSoT."""
    site = models.ForeignKey(Site, db_index=True, related_name='changes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='changes', db_index=True
    )
    change_at = models.DateTimeField(auto_now_add=True, null=False)
    event = models.CharField(
        max_length=10, null=False, choices=EVENT_CHOICES,
    )
    resource_id = models.IntegerField('Resource ID', null=False)
    resource_name = models.CharField(
        'Resource Type', max_length=20, null=False, db_index=True,
        choices=CHANGE_RESOURCE_CHOICES
    )
    _resource = fields.JSONField('Resource', null=False, blank=True)

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
