# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields.json


def migrate_device_fields(apps, schema_editor):
    """
    Migrate new Device fields.
    """
    Device = apps.get_model('nsot', 'Device')
    Device_temp = apps.get_model('nsot', 'Device_temp')
    for dev in Device.objects.iterator():
        dev_tmp = Device_temp.objects.create(
            id=dev.resource_ptr_id,
            hostname=dev.hostname,
            _attributes_cache = dev._attributes,
            site=dev.site,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0015_move_attribute_fields'),
    ]

    operations = [

        # Device _attributes_cache, new_id
        migrations.RunPython(migrate_device_fields),

    ]
