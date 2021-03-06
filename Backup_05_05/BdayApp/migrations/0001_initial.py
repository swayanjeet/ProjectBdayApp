# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-11-16 06:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BdayAppUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_id', models.EmailField(max_length=254, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('creation_date', models.DateTimeField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('admin', models.ManyToManyField(related_name='admin', to='BdayApp.BdayAppUser')),
                ('members', models.ManyToManyField(related_name='members', to='BdayApp.BdayAppUser')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=50)),
                ('profile_pic', models.URLField()),
                ('access_token', models.CharField(max_length=150)),
                ('profile_type', models.CharField(choices=[('FB', 'FACEBOOK'), ('GP', 'GOOGLEPLUS')], max_length=2)),
                ('birthday', models.CharField(max_length=10)),
                ('app_friends', models.ManyToManyField(null=True, related_name='friends', to='BdayApp.BdayAppUser')),
                ('user_id', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_id', to='BdayApp.BdayAppUser')),
            ],
        ),
    ]
