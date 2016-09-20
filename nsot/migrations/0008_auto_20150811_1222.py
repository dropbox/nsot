# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0007_auto_20150811_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='address',
            field=models.ForeignKey(related_name='assignments', to='nsot.Network'),
        ),
    ]
