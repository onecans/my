# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-18 07:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datareader', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodmincnt',
            name='codes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
