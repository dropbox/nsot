# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def update_interface_device_hostname(apps, schema_editor):
    """Update all interfaces with hostname from associated device"""
    Device = apps.get_model('nsot', 'Device')
    for dev in Device.objects.iterator():
        dev.interfaces.update(device_hostname=dev.hostname)


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0027_interface_device_hostname'),
    ]

    operations = [

        # Save all devices
        migrations.RunPython(update_interface_device_hostname),

    ]
