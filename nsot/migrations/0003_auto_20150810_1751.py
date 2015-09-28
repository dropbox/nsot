# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import macaddress.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0002_auto_20150810_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interface',
            name='mac',
            field=macaddress.fields.MACAddressField(db_index=True, integer=True, null=True, blank=True),
        ),
    ]
