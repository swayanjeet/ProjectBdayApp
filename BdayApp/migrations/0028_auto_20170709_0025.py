# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-08 18:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0027_auto_20170708_2328'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='otherlifeevents',
            options={'ordering': ['-created_date']},
        ),
        migrations.AlterField(
            model_name='otherlifeevents',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='other_life_events', to='BdayApp.BdayAppUser'),
        ),
    ]
