# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from nsot.util import slugify


def add_name_slug(apps, schema_editor):
    """ Add a name_slug for every Circuit that doesn't already have one """

    Circuit = apps.get_model('nsot', 'Circuit')
    for c in Circuit.objects.all():
        if not c.name_slug:
            c.name_slug = slugify(c.name)
            c.save()


def remove_name_slug(apps, schema_editor):
    Circuit = apps.get_model('nsot', 'Circuit')
    for c in Circuit.objects.all():
        c.name_slug = None
        c.save()


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0030_add_circuit_name_slug'),
    ]

    operations = [
        migrations.RunPython(add_name_slug, remove_name_slug)
    ]
