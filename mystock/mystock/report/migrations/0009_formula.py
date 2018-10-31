# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-09-25 07:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_group'),
        ('report', '0008_auto_20170925_0335'),
    ]

    operations = [
        migrations.CreateModel(
            name='Formula',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('adds', models.ManyToManyField(related_name='adds', to='report.Item')),
                ('minus', models.ManyToManyField(related_name='minus', to='report.Item')),
                ('report', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='report.Report')),
                ('stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.Stock')),
            ],
        ),
    ]
