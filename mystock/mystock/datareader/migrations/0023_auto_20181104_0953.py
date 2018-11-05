# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-11-04 09:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datareader', '0022_auto_20181104_0927'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pricefallsetup',
            name='high_period_end',
        ),
        migrations.RemoveField(
            model_name='pricefallsetup',
            name='high_period_start',
        ),
        migrations.RemoveField(
            model_name='pricefallsetup',
            name='low_period_end',
        ),
        migrations.RemoveField(
            model_name='pricefallsetup',
            name='low_period_start',
        ),
        migrations.AddField(
            model_name='pricefallsetup',
            name='end',
            field=models.DateField(blank=True, null=True, verbose_name='结束日期'),
        ),
        migrations.AddField(
            model_name='pricefallsetup',
            name='start',
            field=models.DateField(blank=True, null=True, verbose_name='起始日期'),
        ),
    ]
