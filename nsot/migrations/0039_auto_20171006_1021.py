# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0038_remove_iterable_is_resource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iterable',
            name='parent',
            field=models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Iterable', help_text='The parent Iterable', null=True),
        ),
    ]
