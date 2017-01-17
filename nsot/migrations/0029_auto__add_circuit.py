# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0028_populate_interface_device_hostname'),
    ]

    operations = [
        migrations.CreateModel(
            name='Circuit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes_cache', django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True)),
                ('name', models.CharField(default='', help_text="Unique display name of the Circuit. If not provided, defaults to '{device_a}:{interface_a}_{device_z}:{interface_z}'", unique=True, max_length=255)),
                ('endpoint_a', models.OneToOneField(related_name='circuit_a', on_delete=django.db.models.deletion.PROTECT, verbose_name='A-side endpoint Interface', to='nsot.Interface', help_text='Unique ID of Interface at the A-side.')),
                ('site', models.ForeignKey(related_name='circuits', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site', help_text='Unique ID of the Site this Circuit is under.')),
                ('endpoint_z', models.OneToOneField(related_name='circuit_z', null=True, on_delete=django.db.models.deletion.PROTECT, to='nsot.Interface', help_text='Unique ID of Interface at the Z-side.', verbose_name='Z-side endpoint Interface')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Network', 'Network'), ('Circuit', 'Circuit')]),
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource for this Change.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Network', 'Network'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device')]),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource type to which the Value is bound.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Network', 'Network'), ('Attribute', 'Attribute'), ('Site', 'Site'), ('Interface', 'Interface'), ('Circuit', 'Circuit'), ('Device', 'Device')]),
        ),
    ]
