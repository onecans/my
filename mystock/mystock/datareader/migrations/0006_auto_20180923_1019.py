# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-23 10:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datareader', '0005_rangeanalysehelper'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodmincnt',
            name='end_market_size',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='periodmincnt',
            name='where',
            field=models.CharField(choices=[('SH', 'SH'), ('SZ', 'SZ'), ('ALL', 'ALL')], default='ALL', max_length=10),
        ),
    ]
