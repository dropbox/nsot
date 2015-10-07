# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields.json


def migrate_network_fields(apps, schema_editor):
    """
    Migrate new Network fields.
    """
    Network = apps.get_model('nsot', 'Network')
    Network_temp = apps.get_model('nsot', 'Network_temp')
    for net in Network.objects.iterator():
        net_tmp = Network_temp.objects.create(
            network_address=net.network_address,
            broadcast_address=net.broadcast_address,
            prefix_length=net.prefix_length,
            ip_version=net.ip_version,
            is_ip=net.is_ip,
            id=net.resource_ptr_id,
            parent_id=net.parent_id,
            _attributes_cache=net._attributes,
            site=net.site,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0016_move_device_data'),
    ]

    operations = [

        # Network _attributes_cache, new_id
        migrations.RunPython(migrate_network_fields),

    ]
