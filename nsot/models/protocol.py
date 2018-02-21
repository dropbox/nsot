from django.db import models

from .. import exc
from .attribute import Attribute
from .resource import Resource


class Protocol(Resource):
    """
    Representation of a routing protocol
    """
    site = models.ForeignKey(
        'Site', db_index=True, blank=True, null=True, related_name='protocols',
        on_delete=models.PROTECT, verbose_name='Site',
        help_text=(
            'Unique ID of the Site this Protocol is under. If not set, this '
            "be inherited off of the device's site"
        )
    )
    type = models.ForeignKey(
        'ProtocolType', db_index=True, related_name='protocols',
        help_text='The type of this Protocol',
    )
    device = models.ForeignKey(
        'Device', db_index=True, null=False, related_name='protocols',
        help_text='Device that this protocol is running on',
    )
    interface = models.ForeignKey(
        'Interface', db_index=True, blank=True, null=True,
        related_name='protocols',
        help_text=(
            'Interface this protocol is running on. Either interface or'
            ' circuit must be populated.'
        ),
    )
    circuit = models.ForeignKey(
        'Circuit', db_index=True, blank=True, null=True,
        related_name='protocols',
        help_text='Circuit that this protocol is running over.',
    )
    auth_string = models.CharField(
        max_length=255, default='', blank=True, verbose_name='Auth String',
        help_text='Authentication string (such as MD5 sum)',
    )
    description = models.CharField(
        max_length=255, default='', blank=True,
        help_text='Description for this Protocol'
    )

    def __unicode__(self):
        description = unicode(self.type)

        if self.circuit:
            description += ' over %s' % self.circuit
        elif self.interface:
            description += ' on %s' % self.interface
        else:
            description += ' on %s' % self.device

        return description

    class Meta:
        ordering = ('device', )

    def clean_site(self, value):
        """
        Ensure we have a site set. If one is not explicitly set, glean it from
        the device. If the device has none, then raise a ValidationError
        """
        if not value:
            value = self.device.site

        if not value:
            raise exc.ValidationError({
                'site': (
                    'No site was provided and the provided Device does not '
                    'have a site defined'
                )
            })

        return value

    def clean_circuit(self, value):
        """ Ensure at least one endpoint on the circuit is on this device """
        if value and value.interface_for(self.device) is None:
            raise exc.ValidationError({
                'circuit': (
                    'At least one endpoint of the circuit must match the '
                    'device'
                )
            })

        return value

    def clean_interface(self, value):
        """
        Ensure that the interface is bound to the same device this Protocol is
        bound to.
        """
        if value and value.device != self.device:
            raise exc.ValidationError({
                'interface': (
                    'The interface must be on the same device that this'
                    ' Protocol is on'
                )
            })

        return value

    def clean_type(self, value):
        """Ensure that ProtocolType matches our site."""
        if self.site != value.site:
            raise exc.ValidationError({
                'type': 'The type must be on the same site as this Protocol'
            })

        return value

    def set_attributes(self, attributes, valid_attributes=None, partial=False):
        """
        Ensure that all attributes are set that are required by the set
        ProtocolType.
        """
        required = self.type.get_required_attributes()
        if valid_attributes is None:
            valid_attributes = Attribute.all_by_name(
                'Protocol', site=self.site
            )

        # Temporarily mark required attributes as ``required`` at run-time for
        # injecting required_attributes into validation.
        for r in required:
            if r in valid_attributes:
                valid_attributes[r].required = True

        return super(Protocol, self).set_attributes(
            attributes, valid_attributes=valid_attributes,
            partial=partial
        )

    def clean_fields(self, exclude=None):
        self.site = self.clean_site(self.site)
        self.type = self.clean_type(self.type)
        self.interface = self.clean_interface(self.interface)
        self.circuit = self.clean_circuit(self.circuit)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Protocol, self).save(*args, **kwargs)

    # TODO(jathan): type, device, interface, circuit need indexing. We might
    # consider caching these values ON the Protocol object similarly how we've
    # done it with other objects, so that the related lookups are only done on
    # update.
    def to_dict(self):
        return {
            'id': self.id,
            'site': self.site_id,
            'type': self.type.name,
            'device': self.device.hostname,
            'interface': self.interface and self.interface.name_slug,
            'circuit': self.circuit and self.circuit.name_slug,
            'description': self.description,
            'auth_string': self.auth_string,
            'attributes': self.get_attributes(),
        }
