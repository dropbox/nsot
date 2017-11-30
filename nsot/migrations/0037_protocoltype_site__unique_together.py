# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0036_add_protocol'),
    ]

    operations = [
        migrations.AddField(
            model_name='protocoltype',
            name='site',
            field=models.ForeignKey(related_name='protocol_types', on_delete=django.db.models.deletion.PROTECT, default=1, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this ProtocolType is under.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource for this Change.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Protocol', 'Protocol'), ('Network', 'Network'), ('ProtocolType', 'ProtocolType'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device')]),
        ),
        migrations.AlterField(
            model_name='protocol',
            name='auth_string',
            field=models.CharField(default='', help_text='Authentication string (such as MD5 sum)', max_length=255, verbose_name='Auth String', blank=True),
        ),
        migrations.AlterField(
            model_name='protocoltype',
            name='name',
            field=models.CharField(help_text='Name of this type of protocol (e.g. OSPF, BGP, etc.)', max_length=16, db_index=True),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource type to which the Value is bound.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Protocol', 'Protocol'), ('Network', 'Network'), ('Circuit', 'Circuit')]),
        ),
        migrations.AlterUniqueTogether(
            name='protocoltype',
            unique_together=set([('site', 'name')]),
        ),
    ]
