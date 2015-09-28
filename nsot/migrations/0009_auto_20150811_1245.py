# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0008_auto_20150811_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interface',
            name='type',
            field=models.IntegerField(default=6, db_index=True, verbose_name='Interface Type', choices=[(1, 'other'), (6, 'ethernet'), (24, 'loopback'), (131, 'tunnel'), (135, 'l2vlan'), (136, 'l3vlan'), (150, 'mpls'), (161, 'lag')]),
        ),
    ]
