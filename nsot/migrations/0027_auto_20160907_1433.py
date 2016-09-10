# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0026_auto_20160907_1122'),
    ]

    operations = [
        migrations.AddField(
            model_name='iterable',
            name='increment',
            field=models.IntegerField(default=1, help_text='Increment  value  of the Iterable by.'),
        ),
        migrations.AddField(
            model_name='iterable',
            name='max_val',
            field=models.IntegerField(default=100, help_text='The maximum value  of the Iterable.'),
        ),
        migrations.AddField(
            model_name='iterable',
            name='min_val',
            field=models.IntegerField(default=1, help_text='The minimum value of the Iterable.'),
        ),
    ]
