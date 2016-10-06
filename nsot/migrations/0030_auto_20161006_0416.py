# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0029_auto_20161005_1445'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='iterable',
            name='_attributes_cache',
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Itervalue', 'Itervalue'), ('Network', 'Network')]),
        ),
    ]
