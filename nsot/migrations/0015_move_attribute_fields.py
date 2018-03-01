# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django_extensions.db.fields.json
import nsot.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0014_auto_20151002_1653'),
    ]

    operations = [

        ##########
        # Device #
        ##########
        # Create temp Device object
        migrations.CreateModel(
            name='Device_temp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes_cache', django_extensions.db.fields.json.JSONField(blank=True)),
                ('hostname', models.CharField(max_length=255, db_index=True)),
                ('site', models.ForeignKey(related_name='devices', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site')),
            ],
        ),

        # self._attributes_cache = self.resource_ptr._attributes
        migrations.AddField(
            model_name='device',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(blank=True),
        ),

        # self.id = self.resource_ptr_id
        migrations.AddField(
            model_name='device',
            name='new_id',
            field=models.IntegerField(default=0, verbose_name='ID'),
            preserve_default=False,
        ),

        ###########
        # Network #
        ###########
        migrations.CreateModel(
            name='Network_temp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes_cache', django_extensions.db.fields.json.JSONField(blank=True)),
                ('network_address', nsot.fields.BinaryIPAddressField(max_length=16, db_index=True)),
                ('broadcast_address', nsot.fields.BinaryIPAddressField(max_length=16, db_index=True)),
                ('prefix_length', models.IntegerField(db_index=True)),
                ('ip_version', models.CharField(db_index=True, max_length=1, choices=[('4', '4'), ('6', '6')])),
                ('is_ip', models.BooleanField(default=False, db_index=True)),
                ('parent', models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Network_temp', null=True),
        ),
                ('site', models.ForeignKey(related_name='networks', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site')),
            ],
        ),

        migrations.AddField(
            model_name='network',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(blank=True),
        ),
        migrations.AddField(
            model_name='network',
            name='new_id',
            field=models.IntegerField(default=0, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='network',
            name='new_parent_id',
            field=models.IntegerField(null=True, verbose_name='Parent ID'),
            preserve_default=False,
        ),

        ##################
        # Assignment 1/2 #
        ##################

        migrations.CreateModel(
            name='Assignment_temp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.ForeignKey(to='nsot.Network_temp')),
                # ('interface', models.ForeignKey(to='nsot.Interface_temp')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),

        #############
        # Interface #
        #############
        migrations.CreateModel(
            name='Interface_temp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes_cache', django_extensions.db.fields.json.JSONField(blank=True)),
                ('name', models.CharField(help_text='The name of the interface as it appears on the Device.', max_length=255, db_index=True)),
                ('description', models.CharField(default='', help_text='A brief yet helpful description.', max_length=255, blank=True)),
                ('type', models.IntegerField(default=6, help_text="If not provided, defaults to 'ethernet'.", db_index=True, verbose_name='Interface Type', choices=[(6, b'ethernet'), (1, b'other'), (135, b'l2vlan'), (136, b'l3vlan'), (161, b'lag'), (24, b'loopback'), (150, b'mpls'), (53, b'prop_virtual'), (131, b'tunnel')])),
                ('mac_address', nsot.fields.MACAddressField(default=0, blank=True, help_text='If not provided, defaults to 00:00:00:00:00:00.', integer=True, null=True, verbose_name='MAC Address', db_index=True)),
                ('speed', models.IntegerField(default=10000, help_text='Integer of Mbps of interface (e.g. 20000 for 20 Gbps). If not provided, defaults to 10000.', db_index=True, blank=True)),
                ('addresses', models.ManyToManyField(related_name='addresses', through='nsot.Assignment_temp', to='nsot.Network_temp', db_index=True)),
                ('device', models.ForeignKey(related_name='interfaces', verbose_name='Device', to='nsot.Device_temp', help_text='Unique ID of the connected Device.')),
                ('parent', models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, to='nsot.Interface_temp', blank=True, help_text='Unique ID of the parent Interface.', null=True, verbose_name='Parent')),
                ('site', models.ForeignKey(related_name='interfaces', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site')),
            ],
        ),

        migrations.AddField(
            model_name='interface',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(blank=True),
        ),
        migrations.AddField(
            model_name='interface',
            name='new_id',
            field=models.IntegerField(default=0, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='interface',
            name='new_parent_id',
            field=models.IntegerField(null=True, verbose_name='Parent ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='device',
            name='new_device_id',
            field=models.IntegerField(default=0, verbose_name='Device ID'),
            preserve_default=False,
        ),

        ##################
        # Assignment 2/2 # 
        ##################
        migrations.AddField(
            model_name='assignment_temp',
            name='interface',
            field=models.ForeignKey(to='nsot.Interface_temp'),
        ),
        migrations.AlterUniqueTogether(
            name='interface_temp',
            unique_together=set([('device', 'name')]),
        ),
        migrations.AlterIndexTogether(
            name='interface_temp',
            index_together=set([('device', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='assignment_temp',
            unique_together=set([('address', 'interface')]),
        ),
        migrations.AlterIndexTogether(
            name='assignment_temp',
            index_together=set([('address', 'interface')]),
        ),

        #########
        # Value #
        #########

        # self.attribute.name => self.name
        migrations.AddField(
            model_name='value',
            name='name',
            field=models.CharField(max_length=64, verbose_name='Name', blank=True),
        ),

        # self.resource_id => self.new_resource_id
        migrations.AddField(
            model_name='value',
            name='new_resource_id',
            field=models.IntegerField(default=1, verbose_name='Resource ID'),
            preserve_default=False,
        ),

        # self.resource_name = self.resource.__class__.__name__
        migrations.AddField(
            model_name='value',
            name='resource_name',
            field=models.CharField(default='BOGUS', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Device', 'Device'), ('Attribute', 'Attribute'), ('Interface', 'Interface'), ('Site', 'Site'), ('Network', 'Network')]),
            preserve_default=False,
        ),

        ##########
        # Change #
        ##########

        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(db_index=True, max_length=20, verbose_name='Resource Type', choices=[('Device', 'Device'), ('Attribute', 'Attribute'), ('Interface', 'Interface'), ('Site', 'Site'), ('Network', 'Network')]),
        ),

]
