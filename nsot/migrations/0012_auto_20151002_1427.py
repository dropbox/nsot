# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0011_auto_20150930_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interface',
            name='description',
            field=models.CharField(default='', help_text='A brief yet helpful description.', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='device',
            field=models.ForeignKey(related_name='interfaces', verbose_name='Device', to='nsot.Device', help_text='Unique ID of the connected Device.'),
        ),
        migrations.AlterField(
            model_name='interface',
            name='parent',
            field=smart_selects.db_fields.ChainedForeignKey(chained_model_field='device', related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, auto_choose=True, to='nsot.Interface', chained_field='device', blank=True, help_text='Unique ID of the parent Interface.', null=True, verbose_name='Parent'),
        ),
        migrations.AlterField(
            model_name='interface',
            name='type',
            field=models.IntegerField(default=6, help_text="If not provided, defaults to 'ethernet'.", db_index=True, verbose_name='Interface Type', choices=[(6, b'ethernet'), (1, b'other'), (135, b'l2vlan'), (136, b'l3vlan'), (161, b'lag'), (24, b'loopback'), (150, b'mpls'), (53, b'prop_virtual'), (131, b'tunnel')]),
        ),
    ]
