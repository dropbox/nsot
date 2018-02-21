from __future__ import unicode_literals

from django.db import models

from .. import exc, validators


class Assignment(models.Model):
    """
    DB object for assignment of addresses to interfaces (on devices).

    This is used to enforce constraints at the relationship level for addition
    of new address assignments.
    """
    address = models.ForeignKey(
        'Network', related_name='assignments', db_index=True,
        help_text='Network to which this assignment is bound.'
    )
    interface = models.ForeignKey(
        'Interface', related_name='assignments', db_index=True,
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
            'hostname': self.interface.device_hostname,
            'interface': self.interface.id,
            'interface_name': self.interface.name,
            'address': self.address.cidr,
        }
