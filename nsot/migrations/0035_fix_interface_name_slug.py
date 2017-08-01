# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from nsot.util import slugify_interface


def add_name_slug(apps, schema_editor):
    """Correctly name_slug for every Interface with slash in the name."""
    Interface = apps.get_model('nsot', 'Interface')
    for i in Interface.objects.iterator():
        name_slug = slugify_interface(
            device_hostname=i.device_hostname, name=i.name
        )
        i.name_slug = name_slug
        i.save()


def remove_name_slug(apps, schema_editor):
    Interface = apps.get_model('nsot', 'Interface')
    Interface.objects.update(name_slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0034_populate_interface_name_slug'),
    ]

    operations = [
        migrations.RunPython(add_name_slug, remove_name_slug)
    ]
