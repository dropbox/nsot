# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0012_auto_20151002_1427'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interface',
            name='name',
            field=models.CharField(help_text='The name of the interface as it appears on the Device.', max_length=255, db_index=True),
        ),
    ]
