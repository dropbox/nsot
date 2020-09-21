# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("nsot", "0005_auto_20150810_1847"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assignment",
            name="interface",
            field=models.ForeignKey(
                related_name="assignments",
                to="nsot.Interface",
                on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AlterIndexTogether(
            name="assignment",
            index_together=set([("address", "interface")]),
        ),
    ]
