# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0027_auto_20160925_1135'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itervalue',
            options={'verbose_name': 'itervalue'},
        ),
        migrations.AlterField(
            model_name='attribute',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource to which this Attribute is bound.', max_length=20, verbose_name='Resource Name', db_index=True, choices=[('Device', 'Device'), ('Interface', 'Interface'), ('Itervalue', 'Itervalue'), ('Network', 'Network')]),
        ),
        migrations.AlterField(
            model_name='change',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource for this Change.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Network', 'Network'), ('Attribute', 'Attribute'), ('Itervalue', 'Itervalue'), ('Site', 'Site'), ('Interface', 'Interface'), ('Device', 'Device'), ('Iterable', 'Iterable')]),
        ),
        migrations.AlterField(
            model_name='itervalue',
            name='site',
            field=models.ForeignKey(related_name='itervalue', on_delete=django.db.models.deletion.PROTECT, verbose_name='Site', to='nsot.Site', help_text='Unique ID of the Site this Itervalue is under.'),
        ),
        migrations.AlterField(
            model_name='value',
            name='resource_name',
            field=models.CharField(help_text='The name of the Resource type to which the Value is bound.', max_length=20, verbose_name='Resource Type', db_index=True, choices=[('Network', 'Network'), ('Attribute', 'Attribute'), ('Itervalue', 'Itervalue'), ('Site', 'Site'), ('Interface', 'Interface'), ('Device', 'Device'), ('Iterable', 'Iterable')]),
        ),
    ]
