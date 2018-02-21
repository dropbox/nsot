from __future__ import unicode_literals

from django.db import models

from .. import exc
from . import constants
from .attribute import Attribute


class Value(models.Model):
    """Represents a value for an attribute attached to a Resource."""
    attribute = models.ForeignKey(
        'Attribute', related_name='values', db_index=True,
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
        choices=constants.RESOURCE_CHOICES,
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
        'Site', db_index=True, related_name='values',
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
        if value not in constants.VALID_ATTRIBUTE_RESOURCES:
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
