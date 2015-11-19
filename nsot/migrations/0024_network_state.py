# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0023_auto_20151008_1351'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='state',
            field=models.CharField(default='allocated', max_length=20, db_index=True, choices=[('allocated', 'Allocated'), ('assigned', 'Assigned'), ('orphaned', 'Orphaned'), ('reserved', 'Reserved')]),
        ),
    ]
