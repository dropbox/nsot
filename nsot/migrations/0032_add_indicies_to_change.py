# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0031_populate_circuit_name_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='change',
            name='change_at',
            field=models.DateTimeField(help_text='The timestamp of this Change.', auto_now_add=True, db_index=True),
        ),
        migrations.AlterIndexTogether(
            name='change',
            index_together=set([('resource_name', 'resource_id'), ('resource_name', 'event')]),
        ),
    ]
