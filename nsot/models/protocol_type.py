from django.db import models

from .. import exc


class ProtocolType(models.Model):
    """
    Representation of protocol types (e.g. bgp, is-is, ospf, etc.)
    """
    name = models.CharField(
        max_length=16, db_index=True,
        help_text='Name of this type of protocol (e.g. OSPF, BGP, etc.)',
    )
    description = models.CharField(
        max_length=255, default='', blank=True, null=False,
        help_text='A description for this ProtocolType',
    )
    required_attributes = models.ManyToManyField(
        'Attribute', db_index=True, related_name='protocol_types',
        help_text=(
            'All Attributes which are required by this ProtocolType. If a'
            ' Protocol of this type is saved and is missing one of these'
            ' attributes, a ValidationError will be raised.'
        )
    )
    site = models.ForeignKey(
        'Site', db_index=True, related_name='protocol_types',
        on_delete=models.PROTECT, verbose_name='Site',
        help_text='Unique ID of the Site this ProtocolType is under.'
    )

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        unique_together = ('site', 'name')

    def get_required_attributes(self):
        """Return a list of the names of ``self.required_attributes``."""
        # FIXME(jathan): These should probably cached on the model and updated
        # on write. Revisit after we see how performance plays out in practice.
        return list(self.required_attributes.values_list('name', flat=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'required_attributes': self.get_required_attributes(),
            'site': self.site_id,
        }


# Signals
def required_attributes_changed(sender, instance, action, reverse, model,
                                pk_set, **kwargs):
    """
    Signal handler that disallows anything but Protocol attributes to be added
    to a ProtocolType.required_attributes.
    """
    if action == 'pre_add':
        # First filter in Protocol attributes.
        attrs = model.objects.filter(pk__in=pk_set)
        if attrs.exclude(resource_name='Protocol').exists():
            raise exc.ValidationError({
                'required_attributes': 'Only Protocol attributes are allowed'
            })

        # Then make sure that they match the site of the incoming instance.
        wrong_site = attrs.exclude(site_id=instance.site_id)
        if wrong_site.exists():
            bad_attrs = [str(w) for w in wrong_site]
            raise exc.ValidationError({
                'required_attributes': (
                    'Attributes must share the same site as '
                    'ProtocolType.site. Got: %s' % bad_attrs
                )
            })


# Register required_attributes_changed -> ProtocolType.required_attributes
models.signals.m2m_changed.connect(
    required_attributes_changed,
    sender=ProtocolType.required_attributes.through
)
