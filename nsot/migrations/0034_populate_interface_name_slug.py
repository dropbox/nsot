# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def remove_name_slug(apps, schema_editor):
    Interface = apps.get_model('nsot', 'Interface')
    Interface.objects.update(name_slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0033_add_interface_name_slug'),
    ]

    operations = [
        # The "forwards" action was changed to a noop so that migration 0035
        # fully replaces this one without having to do migration gymnastics.
        # Users who previously upgraded to v1.2.0 and had migration 0034
        # already applied will have to apply 0035, but new users will have 0034
        # migration be a noop.
        # In summary:
        # - v1.2.0 =  0033 -> 0034 -> 0035
        # - v1.2.1 =  0033 -> 0035
        migrations.RunPython(migrations.RunPython.noop, remove_name_slug)
    ]
