# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0028_itervalue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itervalue',
            name='iter_key',
            field=models.ForeignKey(to='nsot.Iterable', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
