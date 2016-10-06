# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0028_auto_20161004_0830'),
    ]

    operations = [
        migrations.AddField(
            model_name='iterable',
            name='_attributes_cache',
            field=django_extensions.db.fields.json.JSONField(help_text='Local cache of attributes. (Internal use only)', blank=True),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Itervalue', 'Itervalue'), ('Network', 'Network'), ('Iterable', 'Iterable')]),
        ),
        migrations.AlterField(
            model_name='iterable',
            name='site',
            field=models.ForeignKey(related_name='iterable', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Attribute is under.'),
        ),
    ]
