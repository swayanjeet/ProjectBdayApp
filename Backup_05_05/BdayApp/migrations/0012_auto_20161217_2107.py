# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-17 15:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0011_auto_20161217_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='address',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
