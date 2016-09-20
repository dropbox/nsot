# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0024_network_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='value',
            name='site',
            field=models.ForeignKey(related_name='values', on_delete=django.db.models.deletion.PROTECT, default=1, to='nsot.Site'),
            preserve_default=False,
        ),
    ]
