# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-09-21 08:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0002_auto_20170921_0828'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='quarter',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
