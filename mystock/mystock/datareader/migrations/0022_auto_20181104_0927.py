# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-11-04 09:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datareader', '0021_auto_20181031_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceFallDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fall_range_start', models.FloatField(verbose_name='区间开始')),
                ('fall_range_end', models.FloatField(verbose_name='区间结束')),
                ('codes', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PriceFallSetup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('high_period_start', models.DateField(blank=True, null=True, verbose_name='最高价区间起始日期')),
                ('high_period_end', models.DateField(blank=True, null=True, verbose_name='最高价区间结束日期')),
                ('low_period_start', models.DateField(blank=True, null=True, verbose_name='最低价区间起始日期')),
                ('low_period_end', models.DateField(blank=True, null=True, verbose_name='最低价区间结束日期')),
                ('ranges', models.TextField(blank=True, default='-99999,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,99999', null=True)),
            ],
            options={
                'verbose_name': '跌幅统计设定',
            },
        ),
        migrations.AlterModelOptions(
            name='chgdetail',
            options={'verbose_name': '涨跌幅明细'},
        ),
        migrations.AlterModelOptions(
            name='chgsetup',
            options={'verbose_name': '涨跌幅设定'},
        ),
        migrations.AlterField(
            model_name='chgdetail',
            name='fall',
            field=models.BooleanField(verbose_name='跌幅？'),
        ),
        migrations.AlterField(
            model_name='chgdetail',
            name='fall_range_end',
            field=models.FloatField(verbose_name='区间结束'),
        ),
        migrations.AlterField(
            model_name='chgdetail',
            name='fall_range_start',
            field=models.FloatField(verbose_name='区间开始'),
        ),
        migrations.AlterField(
            model_name='chgdetail',
            name='setup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datareader.ChgSetup', verbose_name='期间设定'),
        ),
        migrations.AddField(
            model_name='pricefalldetail',
            name='setup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datareader.PriceFallSetup', verbose_name='期间设定'),
        ),
    ]