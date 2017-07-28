# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-05-12 09:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0020_auto_20170511_1100'),
    ]

    operations = [
        migrations.AddField(
            model_name='wish',
            name='event',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='BdayApp.Event'),
        ),
        migrations.AlterField(
            model_name='wish',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='BdayApp.BdayAppUser'),
        ),
    ]