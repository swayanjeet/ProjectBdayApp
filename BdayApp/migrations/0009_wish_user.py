# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-12 16:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0008_message_notification_wish'),
    ]

    operations = [
        migrations.AddField(
            model_name='wish',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='BdayApp.BdayAppUser'),
            preserve_default=False,
        ),
    ]
