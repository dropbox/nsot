from __future__ import unicode_literals

from django.db import models

from .. import validators


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
