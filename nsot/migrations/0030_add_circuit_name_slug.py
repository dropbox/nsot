# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0029_auto__add_circuit'),
    ]

    operations = [
        migrations.AddField(
            model_name='circuit',
            name='name_slug',
            field=models.CharField(db_index=True, editable=False, max_length=255, help_text='Slugified version of the name field, used for the natural key', null=True, unique=True),
        ),
    ]
