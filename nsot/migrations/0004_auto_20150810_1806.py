# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import macaddress.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0003_auto_20150810_1751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interface',
            name='mac',
            field=macaddress.fields.MACAddressField(default=0, integer=True, null=True, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='speed',
            field=models.IntegerField(default=1000, db_index=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='type',
            field=models.IntegerField(default=6, db_index=True, verbose_name='Interface Type', choices=[('other', 1), ('ethernet', 6), ('loopback', 24), ('tunnel', 131), ('l2vlan', 135), ('l3vlan', 136), ('mpls', 150), ('lag', 161)]),
        ),
    ]
