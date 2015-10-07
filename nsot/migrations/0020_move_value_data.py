# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_value_fields(apps, schema_editor):
    """
    Migrate new Value fields.
    """
    Value = apps.get_model('nsot', 'Value')
    for val in Value.objects.iterator():
        val.resource_name = val.resource.polymorphic_ctype.model.title()
        val.new_resource_id = val.resource_id
        val.name = val.attribute.name
        val.save()


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0019_move_assignment_data'),
    ]

    operations = [

        # Value name, resource_id, resource_name
        migrations.RunPython(migrate_value_fields),

    ]
