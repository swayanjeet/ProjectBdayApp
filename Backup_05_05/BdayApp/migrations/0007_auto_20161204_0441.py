# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-03 23:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0006_auto_20161129_2018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reminder',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BdayApp.BdayAppUser'),
        ),
    ]
