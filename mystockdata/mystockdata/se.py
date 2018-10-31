import datetime
import json
import os
import time

import pandas as pd
import requests

from mystockdata import config, db
from mystockdata.db import DatetimeIndexMixin, PrefixedDfDb
from mystockdata.exceptions import HistoryDataError


class ShSeDb(DatetimeIndexMixin, PrefixedDfDb):
    prefix = 'sh_se_'


class CybSeDb(DatetimeIndexMixin, PrefixedDfDb):
    prefix = 'cyb_se_'


class SzSeDb(DatetimeIndexMixin, PrefixedDfDb):
    prefix = 'sz_se_'


class SzzbSeDb(DatetimeIndexMixin, PrefixedDfDb,):
    prefix = 'szzb_se_'


class ZxqySeDb(DatetimeIndexMixin, PrefixedDfDb, ):
    prefix = 'zxqy_se_'


class SSE:
    sedb = ShSeDb()

    def read_cache(self):
        df = self.sedb.read()
        return df

    def write_cache(self, df):
        df = self.sedb.save(df)

    def get_sse_overview_day(self):
        '''
           source: http://www.sse.com.cn/market/stockdata/overview/day/
        '''

        def _fetch(date):
            url = ('http://query.sse.com.cn/marketdata/tradedata',
                   '/queryTradingByProdTypeData.do?jsonCallBack=jsonpCallback74321',
                   '&searchDate=[DAY]&prodType=gp&_=1456558103149')
            headers = {
                'Host': 'www.sse.com.cn',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
                'Referer': 'http://www.sse.com.cn/market/stockdata/overview/day/',
            }

            real_url = ''.join(url).replace('[DAY]', date.strftime("%Y-%m-%d"))
            rst = requests.get(url=real_url, headers=headers).text

            json_str = rst[19:len(rst) - 1]

            rst_list = json.loads(json_str)
            rst_list = rst_list['result']

            headers = ['istVol', 'SH_profitRate1', 'SH_negotiableValue1', 'SH_trdAmt1', 'SH_trdVol1', 'SH_trdTm1',
                       'A_istVol', 'A_profitRate1', 'A_negotiableValue1', 'A_trdAmt1', 'A_trdVol1', 'A_trdTm1',
                       'B_istVol', 'B_profitRate1', 'B_negotiableValue1', 'B_trdAmt1', 'B_trdVol1', 'B_trdTm1']

            tmp_dict = dict()

            for key, value in rst_list[0].items():
                tmp_dict['A_' + key] = value if value else None
            for key, value in rst_list[1].items():
                tmp_dict['B_' + key] = value if value else None
            for key, value in rst_list[2].items():
                tmp_dict['SH_' + key] = value if value else None
            return pd.DataFrame([tmp_dict, ], index=[date, ])

        def _fetch_dates(begin, end, to_df=True):
            tmp = []
            print(begin, end)
            dates = pd.date_range(begin, end)
            if len(dates) == 1:
                return None
            for date in dates:

                tmp.append(_fetch(date))
                # print(tmp[-1])
                if len(dates) > 1:
                    print('sleep')
                    time.sleep(0.5)
            # print(pd.concat(tmp))
            return pd.concat(tmp)

        cache_df = self.read_cache()
        if cache_df is None or cache_df.empty:
            raise HistoryDataError()
        else:
            start = max(cache_df.index) + datetime.timedelta(days=-1)
        new_df = _fetch_dates(
            start, datetime.datetime.now())
        if new_df is not None:
            cache_df = cache_df.drop(new_df.index, errors='ignore')
        df = pd.concat([cache_df, new_df])

        if len(df) > len(cache_df):
            self.write_cache(df)
        return df


class SZSE:

    dbs = {'sz': SzSeDb(), 'cyb': CybSeDb(),
           'zxqy': ZxqySeDb(), 'szzb': SzzbSeDb()}

    def read_cache(self, category):
        df = self.dbs[category].read()
        return df

    def write_cache(self, df, category):
        df = self.dbs[category].save(df)

    def get_szse_overview_day(self, category):
        '''
        source: http://www.szse.cn/main/marketdata/tjsj/jbzb/
        '''

        def _fetch(date, category):
            urls = {
                'sz':
                ('http://www.szse.cn/szseWeb/ShowReport.szse?',
                 'SHOWTYPE=EXCEL&CATALOGID=1803&txtQueryDate=%s&ENCODE=1&TABKEY=tab1'),

                #  深圳主板
                'szzb':
                ('http://www.szse.cn/szseWeb/ShowReport.szse?',
                 'SHOWTYPE=EXCEL&CATALOGID=1803&txtQueryDate=%s&ENCODE=1&TABKEY=tab2'),

                #  中小企业板
                'zxqy':
                ('http://www.szse.cn/szseWeb/ShowReport.szse?',
                 'SHOWTYPE=EXCEL&CATALOGID=1803&txtQueryDate=%s&ENCODE=1&TABKEY=tab3'),

                #  创业板
                'cyb':
                ('http://www.szse.cn/szseWeb/ShowReport.szse?',
                 'SHOWTYPE=EXCEL&CATALOGID=1803&txtQueryDate=%s&ENCODE=1&TABKEY=tab4')}
            df = pd.read_html(''.join(urls[category]) % date.strftime(
                "%Y-%m-%d"), encoding='gbk', header=0)[0]
            if df.columns[0] == '没有找到符合条件的数据！':
                return None
            if category in ('szzb', 'cyb', 'zxqy'):
                del df['比上日增减']
                del df['本年最高']
                del df['最高值日期']

            if category == 'sz':
                del df['比上日增减']
                del df['幅度%']
                del df['本年最高']
                del df['最高值日期']

            df = pd.pivot_table(df, columns='指标名称')
            df.index = pd.DatetimeIndex([date.strftime("%Y-%m-%d")])
            return df

        def _fetch_dates(begin, end, category):
            tmp = []
            print(begin, end)
            dates = pd.date_range(begin, end)
            if len(dates) == 1:
                return None
            for date in dates:
                tmp.append(_fetch(date, category))
                if len(dates) > 1:
                    print('sleep')
                    time.sleep(0.5)

            return pd.concat(tmp)

        cache_df = self.read_cache(category)
        if cache_df is None or cache_df.empty:
            raise HistoryDataError()
        else:
            start = max(cache_df.index) + datetime.timedelta(days=-1)
        new_df = _fetch_dates(start, datetime.datetime.now(), category)
        if new_df is not None:
            cache_df = cache_df.drop(new_df.index, errors='ignore')
        df = pd.concat([cache_df, new_df])

        if len(df) > len(cache_df):
            self.write_cache(df, category)
        return df


class SE:

    @classmethod
    def get_overview_day_field(cls, f_sha, f_shb, f_sh, f_sz, f_cyb, f_zxqy, f_szzb):
        sh, sz, cyb, zxqy, szzb = ShSeDb(), SzSeDb(), CybSeDb(), ZxqySeDb(), SzzbSeDb()
        sh = sh.read(columns=[f_sha, f_shb, f_sh])
        sh.columns = ['SHA', 'SHB', 'SH']
        sz = sz.read(columns=[f_sz])
        sz.columns = ['SZ']

        cyb = cyb.read([f_cyb])
        cyb.columns = ['CYB']

        zxqy = zxqy.read([f_zxqy])
        zxqy.columns = ['ZXQY']

        szzb = szzb.read([f_szzb])
        szzb.columns = ['SZZB']

        df = pd.concat([sh, sz, cyb, zxqy, szzb, ], axis=1)
        df = df.fillna(method='bfill')
        return df

    @classmethod
    def get_pe(cls):
        return cls.get_overview_day_field('A_profitRate1', 'B_profitRate1', 'SH_profitRate1',
                                          '股票平均市盈率', '平均市盈率(倍)', '平均市盈率(倍)', '平均市盈率(倍)',)

    @classmethod
    def get_market_val(cls):
        df = cls.get_overview_day_field('A_marketValue1', 'B_marketValue1', 'SH_marketValue1',
                                        '股票总市值（元）', '上市公司市价总值(元)', '上市公司市价总值(元)', '上市公司市价总值(元)',)

        df[['SZ', 'CYB', 'ZXQY']] = df[['SZ', 'CYB', 'ZXQY']] / 100000000
        return df

    @classmethod
    def get_negotiable_val(cls):
        df = cls.get_overview_day_field('A_negotiableValue', 'B_negotiableValue', 'SH_negotiableValue',
                                        '股票流通市值（元）', '上市公司流通市值(元)', '上市公司流通市值(元)', '上市公司流通市值(元)',)
        df[['SZ', 'CYB', 'ZXQY']] = df[['SZ', 'CYB', 'ZXQY']] / 100000000
        return df

    @classmethod
    def get_avg_price(cls):
        sh, sz, cyb, zxqy, szzb = self.get_overview_day()

        sh_a = sh['A_trdAmt'].apply(
            float) * 10000 / sh['A_trdVol'].apply(float)
        sh_a.name = 'SHA'
        sh_b = sh['B_trdAmt'].apply(
            float) * 10000 / sh['B_trdVol'].apply(float)
        sh_b.name = 'SHB'
        sh_sh = sh['SH_trdAmt'].apply(
            float) * 10000 / sh['SH_trdVol'].apply(float)
        sh_sh.name = 'SH'

        sz = sz['平均股票价格（元）']
        sz.name = 'SZ'

        cyb = cyb['总成交金额(元)'] / cyb['总成交股数']
        cyb.name = 'CYB'

        zxqy = zxqy['总成交金额(元)'] / zxqy['总成交股数']
        zxqy.name = 'ZXQY'

        szzb = szzb['总成交金额(元)'] / szzb['总成交股数']
        szzb.name = 'SZZB'

        df = pd.concat([sh_a, sh_b, sh_sh, sz, cyb, zxqy, szzb, ], axis=1)
        return df


def load_old_file():
    def read_file(file):
        path = os.path.abspath(os.path.dirname(__file__))
        df = pd.read_csv(os.path.join(path, file))
        df.index = pd.DatetimeIndex(df.date)
        del df['date']
        return df
    ShSeDb().save(read_file('files/se/sh_sse_day_overview.csv'))
    SzSeDb().save(read_file('files/se/sz_day_overview.csv'))
    CybSeDb().save(read_file('files/se/cyb_day_overview.csv'))
    SzzbSeDb().save(read_file('files/se/szzb_day_overview.csv'))
    ZxqySeDb().save(read_file('files/se/zxqy_day_overview.csv'))

    for key in db.DfDb().keys():
        print(key)
