# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-04-23 04:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0022_auto_20170325_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='type',
            field=models.CharField(default='DEFAULT', max_length=500),
            preserve_default=False,
        ),
    ]
