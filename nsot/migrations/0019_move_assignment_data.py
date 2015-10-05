# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_assignment_fields(apps, schema_editor):
    """Migrate new Assignment fields."""
    Assignment = apps.get_model('nsot', 'Assignment')
    Assignment_temp = apps.get_model('nsot', 'Assignment_temp')
    for asn in Assignment.objects.iterator():
        asn_tmp = Assignment_temp.objects.create(
            id = asn.id,
            address_id=asn.address_id,
            interface_id=asn.interface_id,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0018_move_interface_data'),
    ]

    operations = [

        # Assignment id, address_id, interface_id
        migrations.RunPython(migrate_assignment_fields),

    ]
