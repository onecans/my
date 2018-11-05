# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-11-04 10:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datareader', '0023_auto_20181104_0953'),
    ]

    operations = [
        migrations.AddField(
            model_name='pricefalldetail',
            name='end_market_size',
            field=models.IntegerField(blank=True, null=True, verbose_name='期末股票总数'),
        ),
        migrations.AddField(
            model_name='pricefalldetail',
            name='start_market_size',
            field=models.IntegerField(blank=True, null=True, verbose_name='期初股票总数'),
        ),
    ]
