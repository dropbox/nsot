from __future__ import unicode_literals

import logging

from django.conf import settings
from django.core.cache import cache as djcache
from django.db import models
from django.utils import timezone

from .assignment import Assignment
from .circuit import Circuit
from .device import Device
from .network import Network
from .resource import Resource

from .. import exc, fields, util, validators
from . import constants


log = logging.getLogger(__name__)


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

    # This doesn't use the built-in SlugField since we're doing our own
    # slugification (django.utils.text.slugify() is too agressive)
    name_slug = models.CharField(
        db_index=True, editable=False, max_length=255, null=True, unique=True,
        help_text=(
            'Slugified version of the name field, used for the natural key'
        )
    )

    # if_addr
    # m2m Network object /32 or /128
    addresses = models.ManyToManyField(
        'Network', db_index=True, related_name='addresses',
        through='Assignment',
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
        'Device', db_index=True, related_name='interfaces', null=False,
        verbose_name='Device', help_text='Unique ID of the connected Device.'
    )

    # Cached hostname of the associated device
    device_hostname = models.CharField(
        max_length=255, null=False, blank=True, db_index=True, editable=False,
        help_text=(
            'The hostname of the Device to which the interface is bound. '
            '(Internal use only)'
        )
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
        null=True,
        help_text=(
            'Integer of Mbps of interface (e.g. 20000 for 20 Gbps). If not '
            'provided, defaults to %s.' % settings.INTERFACE_DEFAULT_SPEED
        )
    )

    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children',
        default=None, db_index=True, on_delete=models.PROTECT,
        verbose_name='Parent', help_text='Unique ID of the parent Interface.',
    )

    # We are currently inferring the site_id from the parent Device in the
    # .save() method. We don't want to even care about the site_id , but it
    # simplifies managing them this way.
    site = models.ForeignKey(
        'Site', db_index=True, related_name='interfaces',
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
        return self.name_slug

    class Meta:
        unique_together = ('device', 'name')
        index_together = [
            unique_together,
            ('device_hostname', 'name')
        ]

    @property
    def networks(self):
        """Return all the parent Networks for my addresses."""
        return Network.objects.filter(
            id__in=list(self.addresses.values_list('parent', flat=True))
        ).distinct()

    @property
    def circuit(self):
        """Return the Circuit I am associated with"""
        try:
            return self.circuit_a
        except Circuit.DoesNotExist:
            try:
                return self.circuit_z
            except Circuit.DoesNotExist:
                raise

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

    def get_ancestors(self):
        """Return all ancestors of an Interface."""
        p = self.parent
        ancestors = []
        while p is not None:
            ancestors.append(p.id)
            p = p.parent
        return Interface.objects.filter(id__in=ancestors)

    def get_children(self):
        """Return the immediate children of an Interface."""
        return Interface.objects.filter(parent=self)

    def get_descendants(self):
        """Return all the descendants of an Interface."""
        s = list(self.get_children())
        descendants = []
        while len(s) > 0:
            top = s.pop()
            descendants.append(top.id)
            for c in top.get_children():
                s.append(c)
        return Interface.objects.filter(id__in=descendants)

    def get_root(self):
        """Return the parent of all ancestors of an Interface."""
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    def get_siblings(self):
        """
        Return Interfaces with the same parent and device id as an Interface.
        """
        return Interface.objects.filter(
            parent=self.parent, device=self.device).exclude(id=self.id)

    def get_assignments(self):
        """Return a list of information about my assigned addresses."""
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
        if value is None:
            return value

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
        if value not in constants.INTERFACE_TYPES:
            raise exc.ValidationError({
                'type': 'Invalid type: %r' % value
            })

        return value

    def clean_mac_address(self, value):
        """Enforce valid mac_address."""
        return validators.validate_mac_address(value)

    def clean_device_hostname(self, device):
        """Extract hostname from device"""
        return device.hostname

    def clean_name_slug(self, value=None):
        """Slugify the interface name into natural key."""
        if value is None:
            value = util.slugify_interface(
                device_hostname=self.device_hostname, name=self.name
            )
        return value

    def clean_parent(self, parent):
        if parent is None:
            return parent
        if parent.device_hostname != self.device_hostname:
            raise exc.ValidationError({
                'parent': ("Parent's device does not match device with host "
                           "name %r" % self.device_hostname)
            })
        return parent

    def clean_fields(self, exclude=None):
        self.site_id = self.clean_site(self.site_id)
        self.name = self.clean_name(self.name)
        self.type = self.clean_type(self.type)
        self.speed = self.clean_speed(self.speed)
        self.mac_address = self.clean_mac_address(self.mac_address)
        self.device_hostname = self.clean_device_hostname(self.device)
        self.parent = self.clean_parent(self.parent)
        self.name_slug = self.clean_name_slug()

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
            'parent': self.parent and self.parent.name_slug,
            'name': self.name,
            'name_slug': self.name_slug,
            'device': self.device_id,
            'device_hostname': self.device_hostname,
            'description': self.description,
            'addresses': self.get_addresses(),
            'networks': self.get_networks(),
            'mac_address': self.get_mac_address(),
            'speed': self.speed,
            'type': self.type,
            'attributes': self.get_attributes(),
        }


# Signals
def change_api_updated_at(sender=None, instance=None, *args, **kwargs):
    """Anytime the API is updated, invalidate the cache."""
    djcache.set('api_updated_at_timestamp', timezone.now())


def update_device_interfaces(sender, instance, **kwargs):
    """Anytime a device is saved, update device_hostname on its interfaces"""
    interfaces = Interface.objects.filter(device=instance)
    interfaces.update(device_hostname=instance.hostname)


models.signals.post_save.connect(
    change_api_updated_at, sender=Interface,
    dispatch_uid='invalidate_cache_post_save_interface'
)
models.signals.post_delete.connect(
    change_api_updated_at, sender=Interface,
    dispatch_uid='invalidate_cache_post_delete_interface'
)
models.signals.post_save.connect(
    update_device_interfaces, sender=Device,
    dispatch_uid='update_interface_post_save_device'
)
