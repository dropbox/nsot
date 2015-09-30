# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0010_auto_20150921_2120'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='parent',
        ),
        migrations.AddField(
            model_name='interface',
            name='parent',
            field=models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Interface', null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='parent',
            field=models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Network', null=True),
        ),
    ]
