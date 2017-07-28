# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from nsot.util import slugify


def add_name_slug(apps, schema_editor):
    """ Add a name_slug for every Interface that doesn't already have one """

    Interface = apps.get_model('nsot', 'Interface')
    for i in Interface.objects.filter(name_slug__isnull=True):
        slug = '%s:%s' % (i.device_hostname, i.name)
        i.name_slug = slugify(slug)
        i.save()


def remove_name_slug(apps, schema_editor):
    Interface = apps.get_model('nsot', 'Interface')
    Interface.objects.update(name_slug=None)


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0033_add_interface_name_slug'),
    ]

    operations = [
        migrations.RunPython(add_name_slug, remove_name_slug)
    ]
