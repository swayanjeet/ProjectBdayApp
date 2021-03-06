# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-11-18 12:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0003_auto_20161116_2024'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_date', models.DateField()),
                ('reminder_name', models.CharField(max_length=50)),
                ('event_associated_flag', models.BooleanField(default=False)),
                ('creation_date', models.DateTimeField()),
                ('associated_event', models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='BdayApp.Event')),
            ],
        ),
        migrations.AddField(
            model_name='bdayappuser',
            name='creation_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='creation_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='birthday',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='BdayApp.BdayAppUser'),
        ),
    ]
