# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0037_auto_20171006_0914'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='iterable',
            name='is_resource',
        ),
    ]
