# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-03 15:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0012_auto_20170926_0240'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='quarter',
        ),
        migrations.RemoveField(
            model_name='report',
            name='report_type',
        ),
        migrations.RemoveField(
            model_name='report',
            name='year',
        ),
        migrations.AddField(
            model_name='report',
            name='period',
            field=models.CharField(default='1800-12', max_length=7),
            preserve_default=False,
        ),
    ]
