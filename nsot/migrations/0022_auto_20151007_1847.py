# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations, models
import django_extensions.db.fields.json
import six


class Migration(migrations.Migration):

    dependencies = [
        ("nsot", "0021_remove_resource_object"),
    ]

    operations = [
        migrations.AddField(
            model_name="interface",
            name="_addresses_cache",
            field=django_extensions.db.fields.json.JSONField(
                default=six.text_type("[]"), blank=True
            ),
        ),
        migrations.AddField(
            model_name="interface",
            name="_networks_cache",
            field=django_extensions.db.fields.json.JSONField(
                default=six.text_type("[]"), blank=True
            ),
        ),
    ]
