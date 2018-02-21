from __future__ import unicode_literals

from calendar import timegm
import difflib
import json

from django.apps import apps
from django.conf import settings
from django.db import models

from .. import exc, fields
from . import constants
from .site import Site


class Change(models.Model):
    """Record of all changes in NSoT."""
    site = models.ForeignKey(
        'Site', db_index=True, related_name='changes', verbose_name='Site',
        help_text='Unique ID of the Site this Change is under.'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='changes', db_index=True,
        help_text='The User that initiated this Change.'
    )
    change_at = models.DateTimeField(
        auto_now_add=True, db_index=True, null=False,
        help_text='The timestamp of this Change.'
    )
    event = models.CharField(
        max_length=10, null=False, choices=constants.EVENT_CHOICES,
        help_text='The type of event this Change represents.'
    )
    resource_id = models.IntegerField(
        'Resource ID', null=False,
        help_text='The unique ID of the Resource for this Change.'
    )
    resource_name = models.CharField(
        'Resource Type', max_length=20, null=False, db_index=True,
        choices=constants.CHANGE_RESOURCE_CHOICES,
        help_text='The name of the Resource for this Change.'
    )
    _resource = fields.JSONField(
        'Resource', null=False, blank=True,
        help_text='Local cache of the changed Resource. (Internal use only)'
    )

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.pop('obj', None)
        super(Change, self).__init__(*args, **kwargs)

    class Meta:
        get_latest_by = 'change_at'
        index_together = (
            ('resource_name', 'resource_id'),
            ('resource_name', 'event'),
        )

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
        from ..api import serializers
        serializer_class = resource_name + 'Serializer'
        return getattr(serializers, serializer_class)

    def clean_event(self, value):
        if value not in constants.CHANGE_EVENTS:
            raise exc.ValidationError('Invalid change event: %r.' % value)
        return value

    def clean_resource_name(self, value):
        if value not in constants.VALID_CHANGE_RESOURCES:
            raise exc.ValidationError('Invalid resource name: %r.' % value)
        return value

    def clean_site(self, obj):
        """value in this case is an instance of a model object."""

        # Site doesn't have an id to itself, so if obj is a Site, use it.
        # Otherwise get the value of the `.site`
        return obj if isinstance(obj, Site) else getattr(obj, 'site')

    def clean_fields(self, exclude=None):
        """This will populate the change fields from the incoming object."""
        obj = self._obj
        if obj is None:
            return None

        self.event = self.clean_event(self.event)
        self.resource_name = self.clean_resource_name(obj.__class__.__name__)
        self.resource_id = obj.id
        self.site = self.clean_site(obj)

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

    @property
    def diff(self):
        """
        Return the diff of the JSON representation of the cached copy of a
        Resource with its current instance
        """
        if self.event == 'Create':
            old = ''
        else:
            # Get the Change just ahead of _this_ change because that has the
            # state of the Resource before this Change occurred.
            # TODO(nickpegg): Get rid of this if we change the behavior of
            # Change to store the previous version of the object
            old_change = Change.objects.filter(
                change_at__lt=self.change_at,
                resource_id=self.resource_id,
                resource_name=self.resource_name
            ).order_by(
                '-change_at'
            ).first()
            old = json.dumps(old_change._resource, indent=2, sort_keys=True)

        if self.event == 'Delete':
            current = ''
        else:
            resource = apps.get_model(self._meta.app_label, self.resource_name)
            obj = resource.objects.get(pk=self.resource_id)

            serializer_class = self.get_serializer_for_resource(
                    self.resource_name)
            serializer = serializer_class(obj)
            current = json.dumps(serializer.data, indent=2, sort_keys=True)

        diff = "\n".join(difflib.ndiff(
            old.splitlines(),
            current.splitlines()
        ))

        return diff
