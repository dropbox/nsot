from __future__ import unicode_literals

from django.db import models

from .. import exc, util
from .resource import Resource


class Circuit(Resource):
    """Represents two network Interfaces that are connected"""

    # A-side endpoint interface
    endpoint_a = models.OneToOneField(
        'Interface', on_delete=models.PROTECT, db_index=True, null=False,
        related_name='circuit_a', verbose_name='A-side endpoint Interface',
        help_text='Unique ID of Interface at the A-side.'
    )

    # Z-side endpoint interface
    endpoint_z = models.OneToOneField(
        'Interface', on_delete=models.PROTECT, db_index=True, null=True,
        related_name='circuit_z', verbose_name='Z-side endpoint Interface',
        help_text='Unique ID of Interface at the Z-side.'
    )

    # We are currently inferring the site_id from the parent (A-side) Interface
    # in the .save() method
    site = models.ForeignKey(
        'Site', db_index=True, related_name='circuits',
        on_delete=models.PROTECT,
        help_text='Unique ID of the Site this Circuit is under.'
    )

    name = models.CharField(
        max_length=255, unique=True, default='',
        help_text=(
            'Unique display name of the Circuit. If not provided, defaults to '
            "'{device_a}:{interface_a}_{device_z}:{interface_z}'"
        )
    )

    # This doesn't use the built-in SlugField since we're doing our own
    # slugification (django.utils.text.slugify() is too agressive)
    name_slug = models.CharField(
        db_index=True,
        editable=False,
        max_length=255,
        null=True,
        unique=True,
        help_text=(
            'Slugified version of the name field, used for the natural key'
        )
    )

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        # TODO(jathan): Benchmark queries on a large database to identify
        # whether we need explicit indices for this model. In my initial
        # testing all of the common lookup fields are already indexed so this
        # may not be necessary.
        '''
        index_together = [
            ('endpoint_a', 'endpoint_z'),
            ('site', 'name_slug'),
        ]
        '''

    @property
    def interfaces(self):
        """Return interfaces associated with this circuit."""
        intf_list = [self.endpoint_a, self.endpoint_z]
        return [i for i in intf_list if i is not None]

    @property
    def addresses(self):
        """Return addresses associated with this circuit. This includes addresses
        associated with child interfaces."""
        addresses = []
        for interface in self.interfaces:
            addresses.extend(interface.addresses.all())

            # For each interface, get addresses of all child interfaces and
            # extend the list.
            for child in interface.children.all():
                addresses.extend(child.addresses.all())

        return addresses

    @property
    def devices(self):
        """Return devices associated with this circuit."""
        return [i.device for i in self.interfaces]

    def interface_for(self, device):
        """
        Given a Device object, return the interface attached to this Circuit
        which belongs to that Device. If both ends of the Circuit are attached
        to the Device, the A-side is returned.

        If neither ends of this Circuit are attached to Device, then None is
        returned
        """
        if self.endpoint_a.device == device:
            return self.endpoint_a
        elif self.endpoint_z and self.endpoint_z.device == device:
            return self.endpoint_z
        else:
            return None

    def clean_site(self, value):
        """Always enforce that site is set."""
        if value is None:
            return self.endpoint_a.site_id

        return value

    def clean_endpoint_a(self, value):
        if Circuit.objects.filter(endpoint_z=value).exists():
            raise exc.ValidationError({
                'endpoint_a': 'Interface already used as an endpoint_z'
            })

        return self.endpoint_a

    def clean_endpoint_z(self, value):
        if Circuit.objects.filter(endpoint_a=value).exists():
            raise exc.ValidationError({
                'endpoint_z': 'Interface already used as an endpoint_a'
            })

        return self.endpoint_z

    def clean_name(self, value):
        if value:
            return value

        # Add display name of hostname:intf_hostname:intf
        name = '{}_{}'.format(self.endpoint_a, self.endpoint_z)
        return name

    def clean_fields(self, exclude=None):
        self.site_id = self.clean_site(self.site_id)
        self.endpoint_a = self.clean_endpoint_a(self.endpoint_a_id)
        self.endpoint_z = self.clean_endpoint_z(self.endpoint_z_id)
        self.name = self.clean_name(self.name)

        self.name_slug = util.slugify(self.name)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Circuit, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_slug': self.name_slug,
            'endpoint_a': self.endpoint_a and self.endpoint_a.name_slug,
            'endpoint_z': self.endpoint_z and self.endpoint_z.name_slug,
            'attributes': self.get_attributes(),
        }
