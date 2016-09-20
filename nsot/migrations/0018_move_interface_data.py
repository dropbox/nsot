# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_interface_fields(apps, schema_editor):
    """
    Migrate new Interface fields.
    """
    Interface = apps.get_model('nsot', 'Interface')
    Interface_temp = apps.get_model('nsot', 'Interface_temp')
    for ifc in Interface.objects.iterator():
        ifc_tmp = Interface_temp.objects.create(
            id=ifc.resource_ptr_id,
            name=ifc.name,
            description=ifc.description,
            device_id=ifc.device_id,
            parent_id=ifc.parent_id,
            type=ifc.type,
            speed=ifc.speed,
            mac_address=ifc.mac_address,
            site=ifc.site,
            _attributes_cache = ifc._attributes,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0017_move_network_data'),
    ]

    operations = [

        # Interface _attributes_cache, new_id
        migrations.RunPython(migrate_interface_fields),

    ]
