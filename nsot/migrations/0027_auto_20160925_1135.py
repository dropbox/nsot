# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0026_auto_20160920_1209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itervalue',
            name='unique_id',
        ),
        migrations.AddField(
            model_name='itervalue',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True),
        ),
    ]
