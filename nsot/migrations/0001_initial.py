# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import nsot.util
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
import nsot.fields
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name='email address', db_index=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('secret_key', models.CharField(default=nsot.util.generate_secret_key, max_length=44)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, db_index=True)),
                ('description', models.CharField(default='', max_length=255)),
                ('required', models.BooleanField(default=False)),
                ('display', models.BooleanField(default=False)),
                ('multi', models.BooleanField(default=False)),
                ('constraints', django_extensions.db.fields.json.JSONField(blank=True)),
                ('resource_name', models.CharField(db_index=True, max_length=20, verbose_name='Resource Name', choices=[('Network', 'Network'), ('Device', 'Device')])),
            ],
        ),
        migrations.CreateModel(
            name='Change',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.CharField(max_length=10, choices=[('Create', 'Create'), ('Update', 'Update'), ('Delete', 'Delete')])),
                ('resource_id', models.IntegerField(verbose_name='Resource ID')),
                ('resource_name', models.CharField(db_index=True, max_length=20, verbose_name='Resource Type', choices=[('Device', 'Device'), ('Attribute', 'Attribute'), ('Permission', 'Permission'), ('Site', 'Site'), ('Network', 'Network')])),
                ('_resource', django_extensions.db.fields.json.JSONField(verbose_name='Resource', blank=True)),
            ],
            options={
                'get_latest_by': 'change_at',
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_attributes', django_extensions.db.fields.json.JSONField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField(default='', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(db_index=True, max_length=255, blank=True)),
                ('attribute', models.ForeignKey(related_name='values', on_delete=django.db.models.deletion.PROTECT, to='nsot.Attribute')),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('resource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='nsot.Resource')),
                ('hostname', models.CharField(max_length=255, db_index=True)),
                ('site', models.ForeignKey(related_name='devices', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site')),
            ],
            bases=('nsot.resource',),
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('resource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='nsot.Resource')),
                ('network_address', nsot.fields.BinaryIPAddressField(max_length=16, db_index=True)),
                ('broadcast_address', nsot.fields.BinaryIPAddressField(max_length=16, db_index=True)),
                ('prefix_length', models.IntegerField(db_index=True)),
                ('ip_version', models.CharField(db_index=True, max_length=1, choices=[('4', '4'), ('6', '6')])),
                ('is_ip', models.BooleanField(default=False, db_index=True)),
                ('site', models.ForeignKey(related_name='networks', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site')),
            ],
            bases=('nsot.resource',),
        ),
        migrations.AddField(
            model_name='value',
            name='resource',
            field=models.ForeignKey(related_name='attributes', blank=True, to='nsot.Resource'),
        ),
        migrations.AddField(
            model_name='resource',
            name='parent',
            field=models.ForeignKey(related_name='children', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='nsot.Resource', null=True),
        ),
        migrations.AddField(
            model_name='resource',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_nsot.resource_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='change',
            name='site',
            field=models.ForeignKey(related_name='changes', to='nsot.Site'),
        ),
        migrations.AddField(
            model_name='change',
            name='user',
            field=models.ForeignKey(related_name='changes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='attribute',
            name='site',
            field=models.ForeignKey(related_name='attributes', on_delete=django.db.models.deletion.PROTECT, to='nsot.Site'),
        ),
        migrations.AlterUniqueTogether(
            name='value',
            unique_together=set([('attribute', 'value', 'resource')]),
        ),
        migrations.AlterIndexTogether(
            name='value',
            index_together=set([('attribute', 'value', 'resource')]),
        ),
        migrations.AlterUniqueTogether(
            name='attribute',
            unique_together=set([('site', 'resource_name', 'name')]),
        ),
        migrations.AlterIndexTogether(
            name='attribute',
            index_together=set([('site', 'resource_name', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='network',
            unique_together=set([('site', 'ip_version', 'network_address', 'prefix_length')]),
        ),
        migrations.AlterIndexTogether(
            name='network',
            index_together=set([('site', 'ip_version', 'network_address', 'prefix_length')]),
        ),
        migrations.AlterUniqueTogether(
            name='device',
            unique_together=set([('site', 'hostname')]),
        ),
        migrations.AlterIndexTogether(
            name='device',
            index_together=set([('site', 'hostname')]),
        ),
    ]
