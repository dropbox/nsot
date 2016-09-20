# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import nsot.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0009_auto_20150811_1245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attribute',
            name='description',
            field=models.CharField(default='', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='description',
            field=models.CharField(default='', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='mac_address',
            field=nsot.fields.MACAddressField(default=0, blank=True, help_text='If not provided, defaults to 00:00:00:00:00:00.', integer=True, null=True, verbose_name='MAC Address', db_index=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='name',
            field=models.CharField(help_text='The name of the interface as it appears on the device.', max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='speed',
            field=models.IntegerField(default=10000, help_text='Integer of Mbps of interface (e.g. 20000 for 20 Gbps). If not provided, defaults to 10000.', db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='type',
            field=models.IntegerField(default=6, help_text="If not provided, defaults to 'ethernet'.", db_index=True, verbose_name='Interface Type', choices=[(6, b'ethernet'), (1, b'other'), (135, b'l2vlan'), (136, b'l3vlan'), (161, b'lag'), (24, b'loopback'), (150, b'mpls'), (131, b'tunnel')]),
        ),
    ]
