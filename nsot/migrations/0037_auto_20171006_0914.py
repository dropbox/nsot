# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0036_auto_20171006_0118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource for this Change.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Network', 'Network'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device'), ('Iterable', 'Iterable')]),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource type to which the Value is bound.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Network', 'Network'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device'), ('Iterable', 'Iterable')]),
        ),
    ]
