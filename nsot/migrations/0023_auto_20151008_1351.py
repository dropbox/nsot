# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0022_auto_20151007_1847'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='value',
            index_together=set([('resource_name', 'resource_id'), ('name', 'value', 'resource_name')]),
        ),
    ]
