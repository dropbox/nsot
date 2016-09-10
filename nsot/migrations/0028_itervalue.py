# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0027_auto_20160907_1433'),
    ]

    operations = [
        migrations.CreateModel(
            name='IterValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('val', models.IntegerField(default=1, help_text='The value of the iterable.', unique=True)),
                ('u_id', models.TextField(help_text='A helpful description for the Iterable.', blank=True)),
                ('iter_key', models.ForeignKey(to='nsot.Iterable')),
            ],
        ),
    ]
