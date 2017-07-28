# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-11-29 14:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0005_auto_20161126_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='admin',
            field=models.ManyToManyField(blank=True, null=True, related_name='admin', to='BdayApp.BdayAppUser'),
        ),
        migrations.AlterField(
            model_name='event',
            name='members',
            field=models.ManyToManyField(blank=True, null=True, related_name='members', to='BdayApp.BdayAppUser'),
        ),
    ]
