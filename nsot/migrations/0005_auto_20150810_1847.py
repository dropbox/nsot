# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0004_auto_20150810_1806'),
    ]

    operations = [
        migrations.AddField(
            model_name='interface',
            name='site',
            field=models.ForeignKey(related_name='interfaces', on_delete=django.db.models.deletion.PROTECT, default=1, to='nsot.Site'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(db_index=True, max_length=20, verbose_name='Resource Name', choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Network', 'Network')]),
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(db_index=True, max_length=20, verbose_name='Resource Type', choices=[('Network', 'Network'), ('Permission', 'Permission'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Device', 'Device')]),
        ),
    ]
