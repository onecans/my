# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-04 15:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0003_item_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='value',
            name='period',
            field=models.CharField(max_length=10),
        ),
    ]
