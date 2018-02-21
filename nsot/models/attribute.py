from __future__ import unicode_literals

import re

from django.conf import settings
from django.db import models

from .. import exc, fields, validators
from . import constants


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
        'Site', db_index=True, related_name='attributes',
        on_delete=models.PROTECT, verbose_name='Site',
        help_text='Unique ID of the Site this Attribute is under.'
    )

    resource_name = models.CharField(
        'Resource Name', max_length=20, null=False, db_index=True,
        choices=constants.RESOURCE_CHOICES,
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
        if value not in constants.VALID_ATTRIBUTE_RESOURCES:
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
