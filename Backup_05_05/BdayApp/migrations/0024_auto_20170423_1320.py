# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-04-23 07:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0023_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='event_for_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='event_for_user', to='BdayApp.BdayAppUser'),
        ),
        migrations.AddField(
            model_name='notification',
            name='event_reminder_type',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]