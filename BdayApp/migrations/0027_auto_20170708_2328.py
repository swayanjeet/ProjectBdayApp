# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-08 17:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0026_otherlifeevents'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otherlifeevents',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BdayApp.UserProfile'),
        ),
    ]