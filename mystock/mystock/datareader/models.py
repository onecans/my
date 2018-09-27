import asyncio
import datetime
import math
import operator
import sys
from collections import Counter, defaultdict
from pprint import pprint

import aiohttp
import async_timeout
import click
import numpy as np
import pandas as pd
from django.db import models
from django.utils import timezone

from .services import AioHttpFetch

# Create your models here.

C_WHERE = (('SH', 'SH'), ('SZ', 'SZ'), ('ALL', 'ALL'))


class PeriodMinCnt(models.Model):
    where = models.CharField(max_length=10, default='ALL', choices=C_WHERE)
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(verbose_name='期间末')
    test = models.BooleanField(default=False)
    min_cnt = models.IntegerField(blank=True, null=True, verbose_name='破新低股票数')
    market_size = models.IntegerField(blank=True, null=True,
                                      # label='股票数（平均）'
                                      )
    codes = models.TextField(blank=True, null=True)
    end_market_size = models.IntegerField(blank=True, null=True, verbose_name='期末股票总数')
    start_market_size = models.IntegerField(blank=True, null=True, verbose_name='期初股票总数')

    @property
    def period(self):
        if not self.period_start:
            self.period_start = self.period_end
        return (self.period_start.strftime('%Y-%m-%d'), self.period_end.strftime('%Y-%m-%d'))

    @property
    def profit(self):
        if self.market_size:
            return round(self.min_cnt / self.market_size, 2)
        else:
            return -1

    def _profit_without_new(self):
        if self.start_market_size:
            return round((self.min_cnt - (self.end_market_size - self.start_market_size)) / self.start_market_size, 2)
        else:
            return -1

    _profit_without_new.short_description = '未包含新股比例'
    profit_without_new = property(_profit_without_new)

    def _end_profit(self):
        if self.end_market_size:
            return round(self.min_cnt / self.end_market_size, 2)
        else:
            return -1

    _end_profit.short_description = '包含新股比例（旧）'
    end_profit = property(_end_profit)

<<<<<<< HEAD
    def _new_cnt(self):
        if self.end_market_size and self.start_market_size:
            return self.end_market_size - self.start_market_size
        else:
            return -1
    
    _new_cnt.short_description ='新发行股票数'

    new_cnt = property(_new_cnt)

    def _old_low_cnt(self):
        if self.new_cnt > 0:
            return self.min_cnt - self.new_cnt
        else:
            return -1

    _old_low_cnt.short_description = '老股票破新低的数量'

    old_low_cnt = property(_old_low_cnt)
=======
    # end_profit.descritpon = 'x'
>>>>>>> 7d6ee038d69902d770c53f6ce9f88eb6d520d458

    def get_url(self):
        return '/k/min_max_counter/{code}?resample={resample}&window_size={window_size}&col=low'

    def fetch(self):
        fetch = AioHttpFetch()
        rsts = fetch.x_fetch(self.get_url(), resample='1d', window_size=7*52,
                             min_timetomarket='20370101', test=self.test, where=self.where)
        c = defaultdict(Counter)
        cnt = Counter()
        codes = defaultdict(list)
        period = self.period
        start = period[0]
        end = period[1]

        c_key = '%s===%s' % period
        for rst in rsts:
            for key, value in rst['result'].items():
                if key != 'ismin':
                    continue
                df = pd.DataFrame.from_dict(value, 'index', columns=[key])
                df.index = pd.DatetimeIndex(df.index)

                df = df[df.index <= end]

                if not df.empty:
                    df = df[df.index >= start]

                if not df.empty:
                    cnt[c_key] += 1
                    codes[c_key].append(rst['paras']['code'])
        # print(cnt[key])

        market_size = fetch.x_get_marketsize(where=self.where)

        market_size = pd.DataFrame.from_dict(market_size)
        market_size.index = pd.DatetimeIndex(market_size.index)

        # self.market_size = market_size.loc[end]['cnt']
        print(market_size.loc[start]['cnt'], market_size.loc[end]['cnt'])
        self.market_size = round((market_size.loc[end]['cnt'] + market_size.loc[start]['cnt']) / 2)
        self.end_market_size = market_size.loc[end]['cnt']
        self.start_market_size = market_size.loc[start]['cnt']
        self.min_cnt = cnt[c_key]
        self.codes = ','.join(codes[c_key])
        self.save()
        # print(where, start, ':', end, '|',
        #       '新低:', cnt[key], '股票数:', , '占比:', round(
        #           cnt[key]/market_size.loc[end]['cnt'], 2))
        # print('破新低股票数： ', cnt[key])
        # print('当时', where, '股票数：', market_size.loc[end]['cnt'])
        # print('破新低股票数占比： ', cnt[key]/market_size.loc[end]['cnt'])
        # print('破新低股票列表: ', codes[key])

        # print(codes)


class RangeAnalyse(models.Model):
    where = models.CharField(max_length=10, default='SH', choices=C_WHERE)
    start_period_start = models.DateField()
    start_period_end = models.DateField(blank=True, null=True)

    end_period_start = models.DateField()
    end_period_end = models.DateField(blank=True, null=True)

    test = models.BooleanField(default=False)
    codes = models.TextField(blank=True, null=True)
    cnts = models.TextField(blank=True, null=True)

    decline = models.BooleanField(default=True)

    def get_url(self):
        return '/k/range/{start}/{end}/{code}?start_period_end={start_period_end}&end_period_start={end_period_start}'

    def fetch(self):
        fetch = AioHttpFetch()
        rsts = fetch.x_fetch(self.get_url(), start=self.start_period_start,
                             end=self.end_period_start, start_period_end=self.start_period_end, end_period_start=self.end_period_start,
                             test=self.test, where=self.where)

        cnt = Counter()
        codes = defaultdict(list)

        for rst in rsts:
            for key, value in rst['result'].items():
                if self.decline:
                    if key != 'loser':
                        continue
                else:
                    if key != 'winer':
                        continue
                r = rst['result'][key]['range']
                if r == 999999:
                    continue
                if r == float("inf"):
                    continue
                _key = key + '_' + str(round(r))
                cnt[_key] += 1
                codes[_key].append(rst['paras']['line'].split(':')[0])
        r = [[float(key.split('_')[1]), value]for key, value in cnt.items()]
        self.cnts = sorted(r, key=operator.itemgetter(0))
        self.cnts = '~'.join([':'.join([str(i) for i in cnt]) for cnt in self.cnts])
        self.codes = codes
        self.save()


class RangeAnalyseHelper(models.Model):
    start_period_start = models.CharField(max_length=1000, blank=True, null=True)
    start_period_end = models.CharField(max_length=1000, blank=True, null=True)

    end_period_ends = models.CharField(max_length=1000, blank=True, null=True)

    def save(self, *args, **kwargs):
        for end_period_end in self.end_period_ends.split(','):
            RangeAnalyse(start_period_start=self.start_period_start, start_period_end=self.start_period_end,
                         end_period_end=end_period_end, end_period_start=end_period_end).save()
        # super(RangeAnalyseHelper, self).save(*args, **kwargs)  # Call the real save() method


class MarketDateAnalyseManager(models.Manager):
    def get_url(self):
        return '/k/baseinfo/{code}?col=name,timeToMarket'

    def fetch(self, t='M'):
        if t == 'M':
            substr = 6
            time_format = '%Y%m'
        elif t == 'Y':
            substr = 4
            time_format = '%Y'
        fetch = AioHttpFetch()
        rsts = fetch.x_fetch(self.get_url(),
                             #  test=True
                             )
        cnts = Counter()
        codes = defaultdict(list)
        for rec in rsts:
            code = rec['paras']['code']
            if code in rec['result']['timeToMarket']:

                timeToMarket = rec['result']['timeToMarket'][code]
                if timeToMarket == 0:
                    print(code)
                    continue
                cnts[str(timeToMarket)[:substr]] += 1
                codes[str(timeToMarket)[:substr]].append(code)

        objs = []
        for timeToMarket, cnt in cnts.items():
            d = datetime.datetime.strptime(str(timeToMarket),
                                           time_format)
            # d = datetime.date(d.year, d.month, 1)
            objs.append(MarketDateAnalyse(date=d, cnt=cnt, date_type=t, codes=codes[timeToMarket]))

        if objs:
            self.filter(date_type=t).delete()
            self.bulk_create(objs)


class MarketDateAnalyse(models.Model):
    date = models.DateField()
    cnt = models.IntegerField()
    codes = models.TextField(blank=True, null=True)
    objects = MarketDateAnalyseManager()
    date_type = models.CharField(choices=(('Y', 'year'), ('M', 'month')), default='Y', max_length=10)
    pre_sum_cnt = models.IntegerField(blank=True, null=True)
    sum_cnt = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['date', ]
