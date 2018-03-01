# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0013_auto_20151002_1443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interface',
            name='parent',
            field=models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, to='nsot.Interface', blank=True, help_text='Unique ID of the parent Interface.', null=True, verbose_name='Parent'),
        ),
    ]
