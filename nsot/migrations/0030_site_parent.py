# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0029_auto__add_circuit'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='parent',
            field=models.ForeignKey(related_name='parent_site', on_delete=django.db.models.deletion.PROTECT, verbose_name='Parent site', to='nsot.Site', help_text='ID of a site that this site is nested in', null=True),
        ),
    ]
