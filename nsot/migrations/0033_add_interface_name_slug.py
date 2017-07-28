# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0032_add_indicies_to_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='interface',
            name='name_slug',
            field=models.CharField(null=True, editable=False, max_length=255, help_text='Slugified version of the name field, used for the natural key', unique=True, db_index=True),
        ),
    ]
