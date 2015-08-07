# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import macaddress.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nsot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('address', models.ForeignKey(to='nsot.Network')),
            ],
        ),
        migrations.CreateModel(
            name='Interface',
            fields=[
                ('resource_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='nsot.Resource')),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('description', models.CharField(default='', max_length=255)),
                ('type', models.IntegerField(db_index=True, verbose_name='Interface Type', choices=[('other', 1), ('ethernet', 6), ('loopback', 24), ('tunnel', 131), ('l2vlan', 135), ('l3vlan', 136), ('mpls', 150), ('lag', 161)])),
                ('mac', macaddress.fields.MACAddressField(integer=True, db_index=True, blank=True)),
                ('speed', models.IntegerField(db_index=True)),
                ('addresses', models.ManyToManyField(related_name='addresses', through='nsot.Assignment', to='nsot.Network', db_index=True)),
                ('device', models.ForeignKey(related_name='interfaces', to='nsot.Device')),
            ],
            bases=('nsot.resource',),
        ),
        migrations.AddField(
            model_name='assignment',
            name='interface',
            field=models.ForeignKey(to='nsot.Interface'),
        ),
        migrations.AlterUniqueTogether(
            name='interface',
            unique_together=set([('device', 'name')]),
        ),
        migrations.AlterIndexTogether(
            name='interface',
            index_together=set([('device', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='assignment',
            unique_together=set([('address', 'interface')]),
        ),
    ]
