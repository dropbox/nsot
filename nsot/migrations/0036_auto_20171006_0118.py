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
            name='Iterable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes_cache', django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True)),
                ('name', models.CharField(help_text='The name of the Iterable.', max_length=255, db_index=True)),
                ('description', models.TextField(default='', help_text='A helpful description for the Iterable.', blank=True)),
                ('min_val', models.PositiveIntegerField(default=1, help_text='The minimum value of the Iterable.')),
                ('max_val', models.PositiveIntegerField(default=100, help_text='The maximum value of the Iterable.')),
                ('increment', models.PositiveIntegerField(default=1, help_text='Value to increment the Iterable.')),
                ('is_resource', models.BooleanField(default=False, help_text='Will this resource have children', db_index=True)),
                ('value', models.IntegerField(help_text='Current Value of Iterable', null=True)),
                ('parent', models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Iterable', help_text='The parent DynamicResouce', null=True)),
                ('site', models.ForeignKey(related_name='iterable', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site assigned to this Iterable')),
            ],
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Iterable', 'Iterable'), ('Network', 'Network'), ('Circuit', 'Circuit')]),
        ),
        migrations.AlterField(
            model_name='network',
            name='is_ip',
            field=models.BooleanField(default=False, help_text='Whether the Network is a host address or not.', db_index=True, editable=False),
        ),
        migrations.AlterUniqueTogether(
            name='iterable',
            unique_together=set([('site', 'name', 'value', 'parent')]),
        ),
        migrations.AlterIndexTogether(
            name='iterable',
            index_together=set([('site', 'name', 'value', 'parent')]),
        ),
    ]
