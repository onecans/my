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
import requests
from django.db import models
from django.utils import timezone

from .services import AioHttpFetch

# Create your models here.

C_WHERE = (('SH', 'SH'), ('SZ', 'SZ'), ('ALL', 'ALL'))


class PeriodMinCnt(models.Model):
    where = models.CharField(max_length=10, default='ALL', choices=C_WHERE)
    period_start = models.DateField(blank=True, null=True,verbose_name='期间初')
    period_end = models.DateField(verbose_name='期间末')
    test = models.BooleanField(default=False)
    min_cnt = models.IntegerField(blank=True, null=True, verbose_name='破新低股票数')
    market_size = models.IntegerField(blank=True, null=True,
                                      # label='股票数（平均）'
                                      )
    codes = models.TextField(blank=True, null=True)
    end_market_size = models.IntegerField(blank=True, null=True, verbose_name='期末股票总数')
    start_market_size = models.IntegerField(blank=True, null=True, verbose_name='期初股票总数')
    market_shares_amount = models.FloatField(blank=True, null=True)
    market_liquidity_amount = models.FloatField(blank=True, null=True)
    min_shares_amount = models.FloatField(blank=True, null=True)
    min_liquidity_amount = models.FloatField(blank=True, null=True)
    final = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    def _profit_shares(self):
        if self.market_shares_amount:
            return round(self.min_shares_amount / self.market_shares_amount, 4)
        else:
            return -1

    _profit_shares.short_description = '总市值比例'
    profit_shares = property(_profit_shares)

    def _profit_liquidity(self):
        if self.market_liquidity_amount:
            return round(self.min_liquidity_amount / self.market_liquidity_amount, 4)
        else:
            return -1

    _profit_liquidity.short_description = '流通市值比例'
    profit_liquidity = property(_profit_liquidity)

    @property
    def period(self):
        if not self.period_start:
            self.period_start = self.period_end
        return (self.period_start.strftime('%Y-%m-%d'), self.period_end.strftime('%Y-%m-%d'))

    @property
    def profit(self):
        if self.market_size:
            return round(self.min_cnt / self.market_size, 4)
        else:
            return -1

    def _profit_without_new(self):
        if self.start_market_size:
            return round((self.min_cnt - (self.end_market_size - self.start_market_size)) / self.start_market_size, 4)
        else:
            return -1

    _profit_without_new.short_description = '未包含新股比例'
    profit_without_new = property(_profit_without_new)

    def _end_profit(self):
        if self.end_market_size:
            return round(self.min_cnt / self.end_market_size, 4)
        else:
            return -1

    _end_profit.short_description = '包含新股比例（旧）'
    end_profit = property(_end_profit)

    def _new_cnt(self):
        if self.end_market_size and self.start_market_size:
            return self.end_market_size - self.start_market_size
        else:
            return -1

    _new_cnt.short_description = '新发行股票数'

    new_cnt = property(_new_cnt)

    def _old_low_cnt(self):
        if self.new_cnt > 0:
            return self.min_cnt - self.new_cnt
        else:
            return -1

    _old_low_cnt.short_description = '老股票破新低的数量'

    old_low_cnt = property(_old_low_cnt)

    def get_url(self):
        return '/k/min_counter/{code}?resample={resample}&window_size={window_size}&col=low'

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
        
        # c_key = '%s===%s' % period
        cnt = 0
        codes = []
        sum_shares_amount = 0
        sum_liquidity_amount = 0
        for rst in rsts:
            # key = 'ismin'
            value = rst['result']

            df = pd.DataFrame.from_dict(value)
            df = df[df['ismin'] == True]
            df.index = pd.DatetimeIndex(df.index)

            df = df[df.index <= end]

            if not df.empty:
                df = df[df.index >= start]

            if not df.empty:
                cnt += 1
                codes.append(rst['paras']['line'].split(':')[0])
                
                sum_shares_amount += df['shares_amount'][-1]
                sum_liquidity_amount += df['liquidity_amount'][-1]

        market_size = fetch.x_get_marketsize(where=self.where)

        market_size = pd.DataFrame.from_dict(market_size)
        market_size.index = pd.DatetimeIndex(market_size.index)

        # self.market_size = market_size.loc[end]['cnt']
        print(market_size.loc[start]['cnt'], market_size.loc[end]['cnt'])
        self.market_size = round((market_size.loc[end]['cnt'] + market_size.loc[start]['cnt']) / 2)
        self.end_market_size = market_size.loc[end]['cnt']
        self.start_market_size = market_size.loc[start]['cnt']
        self.min_cnt = cnt
        self.codes = ','.join(codes)
        self.min_shares_amount = sum_shares_amount
        self.min_liquidity_amount = sum_liquidity_amount
        marketinfo = MarketInfo.objects.get(date=self.period_end)
        self.market_liquidity_amount = marketinfo.low_liquidity_amount
        self.market_shares_amount = marketinfo.low_shares_amount
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


class MarketInfoManager(models.Manager):

    def get_url(self):
        return '/market_info/start/end?nocache'

    def refresh(self):
        rst = AioHttpFetch().get(self.get_url())
        objs = []

        lists = [l for l in rst['result'].values()]
        dates = lists[0].keys()
        for row in zip(dates, *[l.values() for l in lists]):
            tmp = {}
            tmp['date'] = row[0]
            for idx, col in enumerate(rst['result'].keys()):
                if col in ('liquidity','shares','is_min','is_max','up_profit',
                'close_liquidity_amount','close_shares_amount','up','market_size','min_liquidity_profit','min_shares_profit',
                'max_liquidity_profit','max_shares_profit','avg_close','low_liquidity_amount','low_shares_amount'):
                    tmp[col] = row[idx+1]
            obj = MarketInfo(**tmp)
            objs.append(obj)

        self.all().delete()
        self.bulk_create(objs)


class MarketInfo(models.Model):
    date = models.DateField(verbose_name='日期')
    liquidity = models.FloatField(blank=True, null=True)
    shares = models.FloatField(blank=True, null=True)
    is_min = models.FloatField(blank=True, null=True, verbose_name='破新低股票数')
    is_max = models.FloatField(blank=True, null=True)
    close_liquidity_amount = models.FloatField(blank=True, null=True)
    close_shares_amount = models.FloatField(blank=True, null=True)
    low_liquidity_amount = models.FloatField(blank=True, null=True)
    low_shares_amount = models.FloatField(blank=True, null=True)
    up = models.FloatField(blank=True, null=True)
    market_size = models.FloatField(blank=True, null=True, verbose_name='股票数')
    avg_close = models.FloatField(blank=True, null=True)
    avg_high = models.FloatField(blank=True, null=True)
    avg_low = models.FloatField(blank=True, null=True)
    up_profit = models.FloatField(blank=True, null=True)
    min_liquidity_profit = models.FloatField(blank=True, null=True,verbose_name='新低流通市值比例')
    min_shares_profit = models.FloatField(blank=True, null=True, verbose_name='新低总市值比例')
    max_liquidity_profit = models.FloatField(blank=True, null=True)
    max_shares_profit = models.FloatField(blank=True, null=True)

    objects = MarketInfoManager()

    class Meta:
        ordering = ['date', ]


class PeriodMinCnt2(models.Model):
    where = models.CharField(max_length=10, default='ALL', choices=C_WHERE,editable=True)
    min_period_start = models.DateField(blank=True, null=True,verbose_name='计算新低起始日期')
    min_period_end = models.DateField(blank=True, null=True, verbose_name='计算新低截止日期')
    period_start = models.DateField(verbose_name='开始日期', blank=True, null=True)
    period_end = models.DateField(verbose_name='截止日期')

    test = models.BooleanField(default=False)
    min_cnt = models.IntegerField(blank=True, null=True, verbose_name='破新低股票数')
    market_size = models.IntegerField(blank=True, null=True,
                                      # label='股票数（平均）'
                                      )
    codes = models.TextField(blank=True, null=True)
    end_market_size = models.IntegerField(blank=True, null=True, verbose_name='期末股票总数')
    start_market_size = models.IntegerField(blank=True, null=True, verbose_name='期初股票总数')
    market_shares_amount = models.FloatField(blank=True, null=True)
    market_liquidity_amount = models.FloatField(blank=True, null=True)
    min_shares_amount = models.FloatField(blank=True, null=True)
    min_liquidity_amount = models.FloatField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    final = models.BooleanField(default=False)
    point_flag = models.BooleanField(default=False, verbose_name='计算定点')


    def save(self, *args, **kwargs):
        if not self.period_start:
            self.period_start =self.period_end
        if not self.min_period_start:
            self.min_period_start = self.period_start + datetime.timedelta(days=-10)
        
        if not self.min_period_end:
            self.min_period_end = self.period_start + datetime.timedelta(days=10)

        
        super(PeriodMinCnt2, self).save(*args, **kwargs) # Call the real save() method

    def _period(self):
        return '%s - %s' % (self.min_period_start.strftime('%Y-%m-%d') , self.min_period_end.strftime('%Y-%m-%d'))

    _period.short_description = '最低点计算期间'
    period = property(_period)


    def _profit_shares(self):
        if self.market_shares_amount:
            return round(self.min_shares_amount / self.market_shares_amount, 4)
        else:
            return -1

    _profit_shares.short_description = '总市值比例'
    profit_shares = property(_profit_shares)

    def _profit_liquidity(self):
        if self.market_liquidity_amount:
            return round(self.min_liquidity_amount / self.market_liquidity_amount, 4)
        else:
            return -1

    _profit_liquidity.short_description = '流通市值比例'
    profit_liquidity = property(_profit_liquidity)

    def _profit_shares2(self):
        if self.market_shares_amount:
            return round(self.min_shares_amount / (self.market_shares_amount - self.min_shares_amount), 4)
        else:
            return -1

    _profit_shares2.short_description = '总市值(新低/未破新低)'
    profit_shares2 = property(_profit_shares2)

    def _profit_liquidity2(self):
        if self.market_liquidity_amount:
            return round(self.min_liquidity_amount / (self.market_liquidity_amount-self.min_liquidity_amount), 4)
        else:
            return -1

    _profit_liquidity2.short_description = '流通市值(新低/未破新低)'
    profit_liquidity2 = property(_profit_liquidity2)


    @property
    def profit(self):
        if self.market_size:
            return round(self.min_cnt / self.market_size, 4)
        else:
            return -1

    def _profit_without_new(self):
        if self.start_market_size:
            return round((self.min_cnt - (self.end_market_size - self.start_market_size)) / self.start_market_size, 4)
        else:
            return -1

    _profit_without_new.short_description = '未包含新股比例'
    profit_without_new = property(_profit_without_new)

    def _end_profit(self):
        if self.end_market_size:
            return round(self.min_cnt / self.end_market_size, 4)
        else:
            return -1

    _end_profit.short_description = '包含新股比例（旧）'
    end_profit = property(_end_profit)

    def _new_cnt(self):
        if self.end_market_size and self.start_market_size:
            return self.end_market_size - self.start_market_size
        else:
            return -1

    _new_cnt.short_description = '新发行股票数'

    new_cnt = property(_new_cnt)

    def _old_low_cnt(self):
        if self.new_cnt > 0:
            return self.min_cnt - self.new_cnt
        else:
            return -1

    _old_low_cnt.short_description = '老股票破新低的数量'

    old_low_cnt = property(_old_low_cnt)

    def get_url(self):
        return '/code_info/start/end/{code}?col=low,shares,liquidity,bfq_low'

    def fetch(self, data=None, market=None):
        dfs = {}
        if data and market:
            dfs = data 
            market_size = market 
        else:
            fetch = AioHttpFetch()
            rsts = fetch.x_fetch(self.get_url(), test=self.test, where=self.where)
            market_size = fetch.x_get_marketsize(where=self.where)
            for rst in rsts:
                dfs[rst['paras']['line'].split(':')[0]] = pd.DataFrame.from_dict(rst['result'])

        c = defaultdict(Counter)
        cnt = Counter()
        codes = defaultdict(list)
        
        # c_key = '%s===%s' % period
        cnt = 0
        codes = []
        sum_shares_amount = 0
        sum_liquidity_amount = 0
        for code, df in dfs.items():
            df = df[(df.index >= self.min_period_start.strftime('%Y-%m-%d'))&(df.index <= self.period_end.strftime('%Y-%m-%d'))] 
            if df.empty:
                continue
            df.index = pd.DatetimeIndex(df.index)

            min_df  = df[(df.index >= self.min_period_start.strftime('%Y-%m-%d'))&(df.index <= self.min_period_end.strftime('%Y-%m-%d'))]

            if min_df.empty:
                start_min_value = df['low'][0]
            else:
                start_min_value = min(min_df['low'])

            if self.point_flag:
                other_df = df.iloc[-1:]
            else:
                other_df =df[(df.index > self.min_period_end.strftime('%Y-%m-%d'))&(df.index <= self.period_end.strftime('%Y-%m-%d'))]
            min_value = min(other_df['low'])

            if min_value <= start_min_value:
                min_idx = other_df['low'].idxmin()
                row = other_df.loc[min_idx] 
                cnt += 1
                codes.append(code)
                
                sum_shares_amount += (row['shares'] * row['bfq_low'] )
                sum_liquidity_amount +=  (row['liquidity'] * row['bfq_low'] )

        

        market_size = pd.DataFrame.from_dict(market_size)
        market_size.index = pd.DatetimeIndex(market_size.index)

        self.market_size = round((market_size.loc[self.period_end]['cnt'] + market_size.loc[self.min_period_start]['cnt']) / 2)
        self.end_market_size = market_size.loc[self.period_end]['cnt']
        self.start_market_size = market_size.loc[self.min_period_start]['cnt']
        self.min_cnt = cnt
        self.codes = ','.join(codes)
        self.min_shares_amount = sum_shares_amount
        self.min_liquidity_amount = sum_liquidity_amount
        marketinfo = MarketInfo.objects.get(date=self.period_end)
        self.market_liquidity_amount = marketinfo.low_liquidity_amount
        self.market_shares_amount = marketinfo.low_shares_amount
        self.save()


class ChgSetup(models.Model):
    start = models.DateField(blank=True, null=True,verbose_name='跌幅计算开始日期')
    end = models.DateField(blank=True, null=True, verbose_name='跌幅计算截止日期')
    step = models.FloatField(default=1.0, verbose_name='倍数步幅')

    class Meta:
        verbose_name = '涨跌幅设定'

    def __str__(self):
        return '[%s ~ %s] %s' % (self.start, self.end, self.step)

    def get_url(self):
        return '/code_info/start/end/{code}?col=low,high'


    def fetch(self, data=None):
        dfs = {}
        if data:
            dfs = data 
        else:
            fetch = AioHttpFetch()
            rsts = fetch.x_fetch(self.get_url(), test=self.test, where=self.where)
            for rst in rsts:
                dfs[rst['paras']['line'].split(':')[0]] = pd.DataFrame.from_dict(rst['result'])
        updd = defaultdict(list)
        falldd = defaultdict(list)
        chg_range = np.arange(0,10000,self.step)
        for code, df in dfs.items():
            df = df[(df.index >= self.start.strftime('%Y-%m-%d'))&(df.index <= self.end.strftime('%Y-%m-%d'))] 
            if df.empty:
                continue
            change = max(df.high) / min(df.low)
            high_idx = df.high.idxmax()
            low_idx = df.low.idxmin()
            if high_idx > low_idx:
                dd = updd
            else:
                dd = falldd
                #涨
            i = 0
            j = 1
            while True:
                if chg_range[i] < change <= chg_range[j]:
                    dd[(chg_range[i],chg_range[j])].append(code)
                    break
                i += 1
                j += 1
        objs = []
        for chg_range, codes in updd.items():
            detail = ChgDetail(setup=self, fall=False, fall_range_start=chg_range[0], fall_range_end=chg_range[1],
            codes = ','.join(codes))
            objs.append(detail)
        
        for chg_range, codes in falldd.items():
            detail = ChgDetail(setup=self, fall=True, fall_range_start=chg_range[0], fall_range_end=chg_range[1],
            codes = ','.join(codes))
            objs.append(detail)
        ChgDetail.objects.filter(setup=self).delete()
        if objs:
            ChgDetail.objects.bulk_create(objs)

         
            

class ChgDetail(models.Model):
    setup = models.ForeignKey(ChgSetup, verbose_name='期间设定')
    fall = models.BooleanField(verbose_name='跌幅？')
    fall_range_start = models.FloatField(verbose_name='区间开始')
    fall_range_end = models.FloatField(verbose_name='区间结束')
    codes = models.TextField(blank=True, null=True)


    class Meta:
        verbose_name = '涨跌幅明细'
