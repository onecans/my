# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-04 15:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0004_auto_20171004_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='value',
            name='stock',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='stock.Stock'),
            preserve_default=False,
        ),
    ]
