from __future__ import unicode_literals

import time
import logging
from operator import attrgetter

from django.conf import settings
from django.db import models
import ipaddress
import netaddr

from .. import exc, fields, util, validators
from . import constants
from .resource import Resource, ResourceManager


log = logging.getLogger(__name__)


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
        lookup_kwargs = util.cidr_to_dict(cidr)
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
        choices=constants.IP_VERSION_CHOICES
    )
    is_ip = models.BooleanField(
        null=False, default=False, db_index=True, editable=False,
        help_text='Whether the Network is a host address or not.'
    )
    site = models.ForeignKey(
        'Site', db_index=True, related_name='networks',
        on_delete=models.PROTECT, verbose_name='Site',
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

    def get_next_network(self, prefix_length, num=None, strict=False,
                         as_objects=True):
        """
        Return a list of the next available networks.

        If no networks are available, an empty list will be returned.

        :param prefix_length:
            The prefix length of networks

        :param num:
            The number of networks desired

        :param as_objects:
            Whether to return IPNetwork objects or strings

        :param strict:
            Whether to return networks for strict allocation

        :returns:
            list(IPNetwork)
        """
        start_time = time.time()  # For debugging

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

        if prefix_length > cidr.max_prefixlen:
            try:
                next(cidr.subnets(new_prefix=prefix_length))
            except ValueError as err:
                raise exc.ValidationError({'prefix_length': err.message})

        if strict:
            children = [c.ip_network for c in self.get_children()]
        else:
            children = [
                c.ip_network for c in self.get_descendants() if (
                    c.prefix_length >= prefix_length
                )
            ]

        exclude_nums = {}

        network_prefix = cidr.network_address

        # Get integer value of network address of parent network shifted
        # (cidr.max_prefixlen - prefix_length) bits to the right
        a = int(network_prefix) >> (cidr.max_prefixlen - prefix_length)

        for c in children:
            # For each child get integer value of network address shifted
            # (cidr.max_prefixlen - prefix_length) bits to the right
            b = int(c.network_address) >> (cidr.max_prefixlen - prefix_length)

            # Get xor of parent network address and child network address this
            # gets rid of the parent network address bits
            d = a ^ b

            # Store the child's prefix length in excluded_nums with the
            # variable d as the key
            if d in exclude_nums:
                # If two children share the same key, then store the shortest
                # prefix length
                if c.prefixlen < exclude_nums[d]:
                    exclude_nums[d] = c.prefixlen
            else:
                exclude_nums[d] = c.prefixlen

        wanted = []

        # Keep a counter starting at integer value of parent network address
        counter = int(cidr.network_address)

        # The upper limit is parent network prefix + 1
        upper = int(cidr.network_address) + 2 ** (cidr.max_prefixlen -
                                                  cidr.prefixlen)

        while counter < upper:
            # If we have requested number of networks then we can break
            if len(wanted) == num:
                break

            if cidr.version == 4:
                next_subnet = ipaddress.IPv4Network((counter, prefix_length))
            else:
                next_subnet = ipaddress.IPv6Network((counter, prefix_length))

            # Shift the bits between parent prefix and requested prefix all the
            # way to the right
            b = counter >> (cidr.max_prefixlen - prefix_length)

            # Remove the parent network address part
            c = a ^ b

            if c in exclude_nums:
                # If this sequence of bits were seen before then we must skip
                # this network
                p = exclude_nums.pop(c)

                if p < prefix_length:
                    # If current network is possibly child of another child
                    # then we must skip overlapping child's range of addresses,
                    # this is so we can implement strict allocation
                    counter += 2 ** (cidr.max_prefixlen - p)
                else:
                    # Otherwise just skip to next network with requested
                    # prefix_length
                    counter += 2 ** (cidr.max_prefixlen - prefix_length)
                continue
            else:
                counter += 2 ** (cidr.max_prefixlen - prefix_length)

            # If this is an interconnect network, we include first and last
            # address in subnet
            if cidr.prefixlen in settings.NETWORK_INTERCONNECT_PREFIXES:
                pass
            elif (
                prefix_length in settings.HOST_PREFIXES and (
                    next_subnet.network_address == cidr.network_address or
                    next_subnet.broadcast_address == cidr.broadcast_address
                )
            ):
                # Otherwise we skip first and last address in subnet
                continue

            # Add network to wanted list
            wanted.append(next_subnet)

        elapsed_time = time.time() - start_time
        log.debug('>> WANTED = %s', wanted)
        log.debug('>> ELAPSED TIME: %s' % elapsed_time)
        return wanted if as_objects else [unicode(w) for w in wanted]

    def get_next_address(self, num=None, strict=False, as_objects=True):
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
            prefix_length=prefix_length, num=num, strict=strict,
            as_objects=as_objects
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

    def get_descendants(self):
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
        return util.get_network_utilization(self)

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

    # Shoutout to jathanism for this code.
    def delete(self, **kwargs):
        force_delete = kwargs.pop('force_delete', False)

        try:
            super(Network, self).delete(**kwargs)
        except exc.ProtectedError as err:
            if force_delete:
                new_parent = self.parent
                # Check if the network does not have a parent, check that it's
                # children are not leaf nodes. If so, raise an error.
                if not new_parent:
                    children = self.get_children()
                    for child in children:
                        if child.is_leaf_node():
                            raise exc.Conflict(
                                'You cannot forcefully delete a network that'
                                'does not have a parent, and whose children '
                                ' are leaf nodes.'
                            )
                # Otherwise, update all children to use the new parent and
                # delete the old parent of these child nodes.
                err.protected_objects.update(parent=new_parent)
                super(Network, self).delete(**kwargs)
            else:
                raise

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
            'cidr': self.cidr,
            'parent_id': self.parent_id,
            'parent': self.parent and self.parent.cidr,
            'site_id': self.site_id,
            'is_ip': self.is_ip,
            'ip_version': self.ip_version,
            'network_address': self.network_address,
            'prefix_length': self.prefix_length,
            'state': self.state,
            'attributes': self.get_attributes(),
        }


# Signals
def refresh_assignment_interface_networks(sender, instance, **kwargs):
    """This signal fires each time a Network object is saved. Upon save,
    the signal iterates through all the child networks of the network
    being saved and cleans the addresses and networks assigned to the
    interfaces (if any) to which these child networks have been assigned.

    We need to clean the addresses on an Interface upon a call to save()
    on Network due to the Interface model caching _addresses & _networks
    which causes the update on the Network object to not cascade onto the
    corresponding Interface object."""
    for child in instance.children.all():
        for assignment in child.assignments.all():
            assignment.interface.clean_addresses()
            assignment.interface.save()


models.signals.post_save.connect(
    refresh_assignment_interface_networks, sender=Network,
    dispatch_uid='refresh_interface_assignment_networks_post_save_network'
)
