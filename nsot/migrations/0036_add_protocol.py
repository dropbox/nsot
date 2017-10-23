# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0035_fix_interface_name_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='Protocol',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes_cache', django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True)),
                ('auth_string', models.CharField(default='', help_text='Authentication string (such as MD5 sum)', max_length=255, blank=True)),
                ('description', models.CharField(default='', help_text='Description for this Protocol', max_length=255, blank=True)),
                ('circuit', models.ForeignKey(related_name='protocols', blank=True, to='nsot.Circuit', help_text='Circuit that this protocol is running over.', null=True)),
                ('device', models.ForeignKey(related_name='protocols', to='nsot.Device', help_text='Device that this protocol is running on')),
                ('interface', models.ForeignKey(related_name='protocols', blank=True, to='nsot.Interface', help_text='Interface this protocol is running on. Either interface or circuit must be populated.', null=True)),
                ('site', models.ForeignKey(related_name='protocols', on_delete=django.db.models.deletion.PROTECT, blank=True, to='nsot.Site', help_text="Unique ID of the Site this Protocol is under. If not set, this be inherited off of the device's site", null=True, verbose_name='Site')),
            ],
            options={
                'ordering': ('device',),
            },
        ),
        migrations.CreateModel(
            name='ProtocolType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Name of this type of protocol (e.g. OSPF, BGP, etc.)', unique=True, max_length=16, db_index=True)),
                ('description', models.CharField(default='', help_text='A description for this ProtocolType', max_length=255, blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Protocol', 'Protocol'), ('Network', 'Network'), ('Circuit', 'Circuit')]),
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource for this Change.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Protocol', 'Protocol'), ('Network', 'Network'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device')]),
        ),
        migrations.AlterField(
            model_name='network',
            name='is_ip',
            field=models.BooleanField(default=False, help_text='Whether the Network is a host address or not.', db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource type to which the Value is bound.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Protocol', 'Protocol'), ('Network', 'Network'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device')]),
        ),
        migrations.AddField(
            model_name='protocoltype',
            name='required_attributes',
            field=models.ManyToManyField(help_text='All Attributes which are required by this ProtocolType. If a Protocol of this type is saved and is missing one of these attributes, a ValidationError will be raised.', related_name='protocol_types', to='nsot.Attribute', db_index=True),
        ),
        migrations.AddField(
            model_name='protocol',
            name='type',
            field=models.ForeignKey(related_name='protocols', to='nsot.ProtocolType', help_text='The type of this Protocol'),
        ),
    ]
