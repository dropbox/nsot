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
                ('type', models.CharField(db_index=True, max_length=8, choices=[(b'bgp', b'BGP'), (b'isis', b'IS-IS'), (b'ospf', b'OSPF')])),
                ('asn', models.PositiveIntegerField(db_index=True)),
                ('auth_string', models.CharField(default='', max_length=255)),
                ('description', models.CharField(default='', max_length=255)),
                ('circuit', models.ForeignKey(related_name='protocols', verbose_name='Circuit that this protocol is running over', to='nsot.Circuit')),
                ('device', models.ForeignKey(related_name='protocols', verbose_name='Device that this protocol is running on', to='nsot.Device')),
                ('site', models.ForeignKey(related_name='protocols', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site', help_text='Unique ID of the Site this Protocol is under.')),
            ],
            options={
                'ordering': ('device', 'asn'),
            },
        ),
    ]
