# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import nsot.fields
import nsot.util.core
import django.db.models.deletion
from django.conf import settings
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0025_value_site'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='address',
            field=models.ForeignKey(related_name='assignments', to='nsot.Network', help_text='Network to which this assignment is bound.'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='interface',
            field=models.ForeignKey(related_name='assignments', to='nsot.Interface', help_text='Interface to which this assignment is bound.'),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='constraints',
            field=django_extensions.db.fields.json.JSONField(help_text='Dictionary of Attribute constraints.', verbose_name='Constraints', blank=True),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='description',
            field=models.CharField(default='', help_text='A helpful description of the Attribute.', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='display',
            field=models.BooleanField(default=False, help_text='Whether the Attribute should be be displayed by default in UIs. If required is set, this is also set.'),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='multi',
            field=models.BooleanField(default=False, help_text='Whether the Attribute should be treated as a list type.'),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='name',
            field=models.CharField(help_text='The name of the Attribute.', max_length=64, db_index=True),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='required',
            field=models.BooleanField(default=False, help_text='Whether the Attribute should be required.'),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Network', 'Network')]),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='site',
            field=models.ForeignKey(related_name='attributes', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Attribute is under.'),
        ),
        migrations.AlterField(
            model_name='change',
            name='_resource',
            field=django_extensions.db.fields.json.JSONField(help_text='Local cache of the changed Resource. (Internal use only)', verbose_name='Resource', blank=True),
        ),
        migrations.AlterField(
            model_name='change',
            name='change_at',
            field=models.DateTimeField(help_text='The timestamp of this Change.', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='change',
            name='event',
            field=models.CharField(help_text='The type of event this Change represents.', max_length=10, choices=[('Create', 'Create'), ('Update', 'Update'), ('Delete', 'Delete')]),
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_id',
            field=models.IntegerField(help_text='The unique ID of the Resource for this Change.', verbose_name='Resource ID'),
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource for this Change.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Device', 'Device'), ('Attribute', 'Attribute'), ('Interface', 'Interface'), ('Site', 'Site'), ('Network', 'Network')]),
        ),
        migrations.AlterField(
            model_name='change',
            name='site',
            field=models.ForeignKey(related_name='changes', verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Change is under.'),
        ),
        migrations.AlterField(
            model_name='change',
            name='user',
            field=models.ForeignKey(related_name='changes', to=settings.AUTH_USER_MODEL, help_text='The User that initiated this Change.'),
        ),
        migrations.AlterField(
            model_name='device',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='hostname',
            field=models.CharField(help_text='The hostname of the Device.', max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='device',
            name='site',
            field=models.ForeignKey(related_name='devices', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Device is under.'),
        ),
        migrations.AlterField(
            model_name='interface',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='addresses',
            field=models.ManyToManyField(help_text='Network addresses assigned to this Interface', related_name='addresses', through='nsot.Assignment', to='nsot.Network', db_index=True),
        ),
        migrations.AlterField(
            model_name='interface',
            name='site',
            field=models.ForeignKey(related_name='interfaces', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site', help_text='Unique ID of the Site this Interface is under.'),
        ),
        migrations.AlterField(
            model_name='interface',
            name='speed',
            field=models.IntegerField(default=1000, help_text='Integer of Mbps of interface (e.g. 20000 for 20 Gbps). If not provided, defaults to 1000.', db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='broadcast_address',
            field=nsot.fields.BinaryIPAddressField(help_text='The broadcast address for the Network. (Internal use only)', max_length=16, db_index=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='is_ip',
            field=models.BooleanField(default=False, help_text='Whether the Network is a host address or not.', db_index=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='network_address',
            field=nsot.fields.BinaryIPAddressField(help_text='The network address for the Network. The network address and the prefix length together uniquely define a network.', max_length=16, verbose_name='Network Address', db_index=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='parent',
            field=models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Network', help_text='The parent Network of the Network.', null=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='prefix_length',
            field=models.IntegerField(help_text='Length of the Network prefix, in bits.', verbose_name='Prefix Length', db_index=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='site',
            field=models.ForeignKey(related_name='networks', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Network is under.'),
        ),
        migrations.AlterField(
            model_name='network',
            name='state',
            field=models.CharField(default='allocated', help_text='The allocation state of the Network.', max_length=20, db_index=True, choices=[('allocated', 'Allocated'), ('assigned', 'Assigned'), ('orphaned', 'Orphaned'), ('reserved', 'Reserved')]),
        ),
        migrations.AlterField(
            model_name='site',
            name='description',
            field=models.TextField(default='', help_text='A helpful description for the Site.', blank=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='name',
            field=models.CharField(help_text='The name of the Site.', unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='user',
            name='secret_key',
            field=models.CharField(default=nsot.util.core.generate_secret_key, help_text="The user's secret_key used for API authentication.", max_length=44),
        ),
        migrations.AlterField(
            model_name='value',
            name='attribute',
            field=models.ForeignKey(related_name='values', on_delete=django.db.models.deletion.PROTECT, to='nsot.Attribute', help_text='The Attribute to which this Value is assigned.'),
        ),
        migrations.AlterField(
            model_name='value',
            name='name',
            field=models.CharField(help_text='The name of the Attribute to which the Value is bound. (Internal use only)', max_length=64, verbose_name='Name', blank=True),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_id',
            field=models.IntegerField(help_text='The unique ID of the Resource to which the Value is bound.', verbose_name='Resource ID'),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource type to which the Value is bound.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Device', 'Device'), ('Attribute', 'Attribute'), ('Interface', 'Interface'), ('Site', 'Site'), ('Network', 'Network')]),
        ),
        migrations.AlterField(
            model_name='value',
            name='site',
            field=models.ForeignKey(related_name='values', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Value is under.'),
        ),
        migrations.AlterField(
            model_name='value',
            name='value',
            field=models.CharField(help_text='The Attribute value.', max_length=255, db_index=True, blank=True),
        ),
    ]
