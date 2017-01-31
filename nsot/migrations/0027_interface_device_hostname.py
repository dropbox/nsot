# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0026_model_field_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='interface',
            name='device_hostname',
            field=models.CharField(help_text='The hostname of the Device to which the interface is bound. (Internal use only)', max_length=255, db_index=True, blank=True, editable=False),
        ),
        migrations.AlterIndexTogether(
            name='interface',
            index_together=set([('device_hostname', 'name'), ('device', 'name')]),
        ),
    ]
