# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-03-25 11:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BdayApp', '0021_auto_20170325_1653'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='checksum_hash',
            new_name='order_id',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='external_response_code',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='external_response_message',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='mid',
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('S', 'TXN_SUCCESS'), ('P', 'PENDING'), ('F', 'TXN_FAILURE'), ('O', 'OPEN')], max_length=20),
        ),
    ]