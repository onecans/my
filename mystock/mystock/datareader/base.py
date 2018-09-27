import base64
import datetime
import functools
import glob
import json
import os
import pathlib
import random
import time
import zipfile
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor as ProcessPoolExecutor
from hashlib import md5

import numpy as np
import pandas as pd
import requests
from django.conf import settings
from django.core.cache import cache
from pytdx.reader.history_financial_reader import HistoryFinancialReader

from datareader.backend.fin import get_fin

# _orgin_read_csv = pd.read_csv
# def _read_csv(*args, **kwargs):
#     _args = '~'.join( [str(arg) for arg in args])
#     _kwargs = '~'.join( ['%s:%s' % (str(key), str(value)) for key,value in kwargs.items()])

#     _cache_key = _args +  '|' + _kwargs
#     _cache_key = _cache_key.replace('\t','/t')
#     # _cache_key = '_read_csv_' + str(base64.encodebytes(bytes(_cache_key, encoding='utf8')))


#     if 'nrows' in kwargs.keys():
#         return _orgin_read_csv(*args, **kwargs)


#     c = cache.get(_cache_key)
#     if c is not None:
#         print(_cache_key, 'Cached')
#         return c
#     print(_cache_key, 'Not Cached')
#     rst = _orgin_read_csv(*args, **kwargs)
#     cache.set(_cache_key, rst)
#     return rst

# pd.read_csv = _read_csv

def cache_df(func):
    def warped(self, *args, **kwargs):
        _args = [str(arg) for arg in args]
        _kwargs = ['%s~%s' % (str(key), str(value)) for key, value in kwargs.items()]
        csv_file = '-'.join(_args) + '__' + '--'.join(_kwargs)
        csv_path = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'tdx_cache' / f'{csv_file}'
        if csv_path.exists():
            tmp = pd.read_feather(csv_path)
            tmp.index = pd.DatetimeIndex(tmp['date'])
            del tmp['date']
            return tmp

        tmp = func(self, *args, **kwargs)
        tmp.reset_index(inplace=True)
        tmp.to_feather(csv_path)
        tmp.index = pd.DatetimeIndex(tmp['date'])
        return tmp

    return warped


class BaseStockDataBackend(object):
    col_mapping = {
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'}

    FQ_TYPE = 'qfq'
    NULL_VALUE = 0
    MARKET_SIZE = 0

    def __init__(self, *args, **kwargs):
        self.se = SE()
        self.rzrq = RZRQ()
        self.tdx = TDX()

    def _get_df(self, code, start=None, end=None, index=False, cache=True):
        raise NotImplementedError()

    def get_list(self, where='', sample=None):
        raise NotImplementedError()

    def get_sh_list(self, sample=None):
        return get_list('SH', sample)

    def get_sz_list(self, sample=None):
        return get_list('SZ', sample)

    def get_df(self, code, start=None, end=None, index=False):
        return self._get_df(code, start, end, index)

    def get_df_val(self,   code, start=None, end=None, val_name=None, **kwargs):
        df = self._get_df(code, start, end)

        if df is not None and not df.empty:
            tmp = df
            for val in val_name.split('.'):
                obj = getattr(tmp, val)
                if callable(obj):
                    tmp = obj()
                else:
                    tmp = obj

            return tmp
        else:
            return kwargs['NULL_VALUE'] if 'NULL_VALUE' in kwargs else self.NULL_VALUE

    def get_week_qfq(self, code, start=None, end=None, index=False, cache=True):
        df = self.get_df(code, start, end, index, cache)

        def take_first(array_like):
            return array_like[0]

        def take_last(array_like):
            return array_like[-1]

        return df.resample('W',                                 # Weekly resample
                           how={'open': 'first',
                                'high': 'max',
                                'low': 'min',
                                'close': 'last',
                                'volume': 'sum'},
                           loffset=pd.offsets.timedelta(days=-6))  # to put the labels to Monday

    def get_pct_change_cumprod(self, code, start, end):
        df = self._get_df(code, start, end)
        df = (1 + df.pct_change()).cumprod() - 1

        if df is not None and not df.empty:
            df.iloc[0] = 0

        return df

    def get_max_range(self, code, start, end, down=True):
        df = self.get_pct_change_cumprod(code, start, end)
        if df is not None and not df.empty:
            if down:
                return min(df.high)
            else:
                return max(df.high)

        return 0

    def get_max_range2(self, code, start, end):
        '''
        跌幅
        '''
        df = self._get_df(code, start, end)

        if df is not None and not df.empty:
            max_high = max(df.high)
            max_high_idx = df.high.idxmax()
            min_low = min(df[df.index >= max_high_idx].low)

            return round(max_high / min_low, 1)

        return 0

    def get_current_range2(self, code, start, end):
        '''
        跌幅
        '''
        df = self._get_df(code, start, end)

        if df is not None and not df.empty:
            max_high = max(df.high)
            max_high_idx = df.high.idxmax()
            current_high = df.high[-1]
            return round(max_high / current_high, 1)

        return 0

    def get_max_grow_range2(self, code, start, end):
        '''
        跌幅
        '''
        df = self._get_df(code, start, end)

        if df is not None and not df.empty:
            min_low = min(df.low)
            min_low_idx = df.low.idxmin()
            max_high = max(df[df.index >= min_low_idx].high)

            return round(max_high / min_low, 1)

        return 0

    def get_current_grow_range2(self, code, start, end):
        '''
        跌幅
        '''
        df = self._get_df(code, start, end)

        if df is not None and not df.empty:
            min_low = min(df.low)
            # max_high_idx = df.high.idxmax()
            current_high = df.high[-1]
            return round(current_high / min_low, 1)

        return 0

    def get_current_range(self, code, start, end):
        df = self.get_pct_change_cumprod(code, start, end)
        if df is not None and not df.empty:
            return df.high[-1]
        else:
            return 0

    # def all_current_range(self, start, end, sample=None, where=None):
    #     codes = self.get_list(where=where,  sample=sample, end=end)

    #     df = pd.DataFrame([{'range': self.get_current_range2(
    #         code, start, end)}for code in codes], index=codes)
    #     return df

    # def all_max_range(self, start, end, sample=None, where=None):
    #     codes = self.get_list(where=where,  sample=sample, end=end)
    #     df = pd.DataFrame([{'range': self.get_max_range2(
    #         code, start, end)}for code in codes], index=codes)
    #     return df

    def all(self, method, start, end, sample=None, where=None, **kwargs):
        codes = self.get_list(where=where,  sample=sample, end=end)
        mtd = getattr(self, method)
        # with ProcessPoolExecutor(max_workers=4) as pool:
        #     rst = [{'code': code, 'val': pool.submit(mtd, code, start, end, **kwargs)} for code in codes]

        # for rec in rst:
        #     rec['val'] = rec['val'].result()

        rst = [{'code': code, 'val': mtd(code, start, end, **kwargs)} for code in codes]

        df = pd.DataFrame.from_dict(rst)
        df.set_index('code', inplace=True)

        # df = pd.DataFrame([{'val': mtd(code, start, end)} for code in codes],
        #                   index=codes)
        return df

    def get_stock_basic(self):
        import pathlib
        csv_file = pathlib.Path('/data/stock/ts/stock_basics.csv')
        if not csv_file.exists():
            import tushare as ts
            ts.get_stock_basics().to_csv(csv_file)

        df = pd.read_csv(csv_file, dtype={'code': np.str})
        df = df.set_index('code')
        return df

    def get_today_all(self):
        import pathlib
        csv_file = pathlib.Path('/data/stock/ts/today_all.csv')
        if not csv_file.exists():
            import tushare as ts
            ts.get_today_all().to_csv(csv_file)

        df = pd.read_csv(csv_file, dtype={'code': np.str})

        df = df.set_index('code')
        return df

    def get_stock_basic_info(self, field):
        '''
        code,代码
        name,名称
        industry,所属行业
        area,地区
        pe,市盈率
        outstanding,流通股本(亿)
        totals,总股本(亿)
        totalAssets,总资产(万)
        liquidAssets,流动资产
        fixedAssets,固定资产
        reserved,公积金
        reservedPerShare,每股公积金
        esp,每股收益
        bvps,每股净资
        pb,市净率
        timeToMarket,上市日期
        undp,未分利润
        perundp, 每股未分配
        rev,收入同比(%)
        profit,利润同比(%)
        gpr,毛利率(%)
        npr,净利润率(%)
        holders,股东人数
        '''
        df = self.get_stock_basic()
        return getattr(df, field)

    def get_market_val(self):
        basic = self.get_stock_basic()
        today = self.get_today_all()

        return basic['totals'] * today['trade']

    # def get_stock_cnt(self):
    #     import datetime
    #     basic = self.get_stock_basic()

    #     basic.drop(basic[basic['timeToMarket'] == 0].index, inplace=True)

    #     df3 = pd.DataFrame(index=basic['timeToMarket'].apply(lambda x: datetime.datetime.strptime(str(x), '%Y%m%d')))
    #     # df3 = df3.drop(df3[df3['timeToMarket'] == '0'].index)
    #     # df3['code'] = df3.index
    #     # df3.index = pd.DatetimeIndex(df3.timeToMarket)
    #     # del df3['timeToMarket']
    #     return df3.groupby(level=0).size().cumsum()

    def handler_df(self, df):
        '''
        增加可读的市值，名称等信息
        '''
        df['market_val'] = self.get_market_val()
        df['name'] = self.get_name()


class TDXDataBackend(BaseStockDataBackend):
    TDX_STOCK_DIR = settings.TDX_STOCK_DIR

    def _get_df_inner(self, code, start=None, end=None, index=False,  nrows=None):
        path = pathlib.Path(self.TDX_STOCK_DIR)
        path = path / self.FQ_TYPE
        if index:
            if code.startswith('3'):
                file_path = path / f'SZ#{code}.txt'
            else:
                file_path = path / f'SH#{code}.txt'
        else:
            file_path = path / f'SH#{code}.txt'

            if not file_path.exists():
                file_path = path / f'SZ#{code}.txt'

        if not file_path.exists():
            return None
        print('read from file:', file_path)
        if not nrows:
            df = pd.read_csv(file_path, skipfooter=1, skiprows=1,
                             engine='python', encoding='gbk', sep='\t')
        else:
            df = pd.read_csv(file_path, skiprows=1, engine='python',
                             encoding='gbk', sep='\t', nrows=nrows)

        # if index:
        #     df.drop(df.columns[6:], axis=1, inplace=True)
        #     df[6] = 0

        try:
            df.columns = ['date', 'open', 'high',
                          'low', 'close', 'volume', 'amount']
            df.index = pd.DatetimeIndex(df['date'])
            del df['date']
        except:
            if not nrows:
                raise
            return None

        if start:
            df = df[df.index >= start]

        if end:
            df = df[df.index <= end]
        return df

    def _get_df(self, code, start=None, end=None, index=False,  nrows=None):

        _cache_key = '.'.join([code, str(index)])
        c = cache.get(_cache_key)
        if c is not None:
            df = c
            print(_cache_key, 'cached')
        else:
            print(_cache_key, 'not cached')
            df = self._get_df_inner(code, index=index)
            cache.set(_cache_key, df)

        if start:
            df = df[df.index >= start]

        if end:
            df = df[df.index <= end]

        if nrows:
            df = df.head(nrows)

        return df

    def get_list(self, where='', sample=None, end=None):

        def filter_end(l):
            tmp = []
            for code in l:
                df = self._get_df(code, nrows=1)
                if df is None:
                    continue
                if df.empty:
                    continue
                if df.index[0] < pd.DatetimeIndex([end, ])[0]:
                    tmp.append(code)
            return tmp

        def filter_market_val(l):
            market_value = self.get_market_val().fillna(0).sort_values()[-1 * self.MARKET_SIZE:]
            tmp = []
            for code in l:
                if code in market_value.index:
                    tmp.append(code)
            return tmp

        path = pathlib.Path(self.TDX_STOCK_DIR) / 'qfq'

        _cache_key = '~'.join(['get_list', str(path), where, str(sample), str(end)])

        c = cache.get(_cache_key)
        if c is not None:
            return c

        rst = [f.name.split('#')[1].split('.')[0]
               for f in path.glob(f'{where}*.txt') if f.name.find('#') >= 0]

        if sample:
            return random.sample(rst, sample)

        if end:
            rst = filter_end(rst)

        if self.MARKET_SIZE:
            rst = filter_market_val(rst)

        print('处理数量：', len(rst))

        cache.set(_cache_key, rst)

        return rst

    def get_base_info(self):
        path = pathlib.Path(self.TDX_STOCK_DIR) / 'qfq' / '沪深Ａ股*.txt'
        _path = sorted(glob.glob(str(path)))[-1]

        _cache_key = '~'.join(['get_base_info', str(path), ])

        c = cache.get(_cache_key)
        if c is not None:
            return c

        df = pd.read_csv(_path, sep='\t', encoding='gbk', skipfooter=1, engine='python', dtype={'代码': np.str})
        df.set_index('代码', inplace=True)

        cache.set(_cache_key, df)
        return df

    def get_market_val(self):
        df = self.get_base_info()['AB股总市值']
        return df.apply(lambda x: float(x.replace('亿', '').replace('--', '0').strip()))

    def get_name(self):
        return self.get_base_info()['名称']

    def get_hangye(self):
        return self.get_base_info()['细分行业']

    def get_pe_ttm(self):
        return self.get_base_info()['市盈(TTM)'].apply(lambda x: float(x.replace('-- ','0')))

    def get_pe_d(self):
        return self.get_base_info()['市盈(动)'].apply(lambda x: float(x.replace('-- ','0')))

    def get_guben(self):
        return self.get_market_val()/self.get_price()


    def get_per_profit(self, pe_type='D'):
        if pe_type == 'TTM':
            pe = self.get_pe_ttm()
        elif pe_type == 'D':
            pe = self.get_pe_d()
        else:
            pe = self.get_pe()
        
        return self.get_price() / pe

    def get_pe(self):
        return self.get_base_info()['市盈(静)'].apply(lambda x: float(x.replace('-- ','0')))

    def get_price(self):
        return self.get_base_info()['现价']

    @cache_df
    def get_all(self, field, *, where='', sample=None):
        df = pd.DataFrame(index=pd.date_range('19990101', datetime.datetime.now()))
        for code in self.get_list(where=where, sample=sample):
            tmp = self.get_df(code)
            df[code] = tmp[field]
        return df

    def get_fin(self, year, quarter):
        return get_fin(year, quarter)


class SSE:

    def get_sse_overview_day(self):
        '''
           source: http://www.sse.com.cn/market/stockdata/overview/day/
        '''

        def _fetch(date, to_df=True):
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
                tmp_dict['A_' + key] = value
            for key, value in rst_list[1].items():
                tmp_dict['B_' + key] = value
            for key, value in rst_list[2].items():
                tmp_dict['SH_' + key] = value
            if to_df:
                return pd.DataFrame([tmp_dict, ], index=[date, ])
            else:
                tmp_dict['date'] = date
                return tmp_dict

        def _fetch_dates(begin, end, to_df=True):
            tmp = []
            print(begin, end)
            dates = pd.date_range(begin, end)
            if len(dates) == 1:
                return None
            for date in dates:
                tmp.append(_fetch(date))
                if len(dates) > 1:
                    print('sleep')
                    time.sleep(0.5)

            return pd.concat(tmp)

        def read_cache():
            p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'sse' / 'sh_sse_day_overview.csv'
            df = pd.read_csv(str(p), index_col='date')
            df.index = pd.DatetimeIndex(df.index)
            return df

        def write_cache(df):
            p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'sse' / 'sh_sse_day_overview.csv'
            df.to_csv(str(p), index_label='date')

        cache_df = read_cache()
        new_df = _fetch_dates(max(cache_df.index) + datetime.timedelta(days=0), datetime.datetime.now())
        if new_df is not None:
            cache_df = cache_df.drop(new_df.index, errors='ignore')
        df = pd.concat([cache_df, new_df])

        if len(df) > len(cache_df):
            write_cache(df)
        return df


class SZSE:
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
            df = pd.read_html(''.join(urls[category]) % date.strftime("%Y-%m-%d"), encoding='gbk', header=0)[0]
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

        def read_cache(category):
            p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'szse' / f'{category}_day_overview.csv'
            df = pd.read_csv(str(p), index_col='date')
            df.index = pd.DatetimeIndex(df.index)
            return df

        def write_cache(df, category):
            p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'szse' / f'{category}_day_overview.csv'
            df.to_csv(str(p), index_label='date')

        cache_df = read_cache(category)
        new_df = _fetch_dates(max(cache_df.index) + datetime.timedelta(days=0), datetime.datetime.now(), category)
        if new_df is not None:
            cache_df = cache_df.drop(new_df.index, errors='ignore')
        df = pd.concat([cache_df, new_df])

        if len(df) > len(cache_df):
            write_cache(df, category)
        return df


class SE:
    def __init__(self, *args, **kwargs):
        self.szse = SZSE()
        self.sse = SSE()

    def fetch(self):
        _ = self.sse.get_sse_overview_day()
        for c in ('sz', 'cyb', 'zxqy', 'szzb'):
            _ = self.szse.get_szse_overview_day(c)

    def get_overview_day(self):
        _cache_key = 'SE_get_overview_day'
        c = cache.get(_cache_key)
        if c is not None:
            return c

        rst = [self.sse.get_sse_overview_day(),
               self.szse.get_szse_overview_day('sz'),
               self.szse.get_szse_overview_day('cyb'),
               self.szse.get_szse_overview_day('zxqy'),
               self.szse.get_szse_overview_day('szzb')]

        cache.set(_cache_key, rst)
        return rst

    def get_overview_day_field(self, f_sha, f_shb, f_sh, f_sz, f_cyb, f_zxqy, f_szzb):
        sh, sz, cyb, zxqy, szzb = self.get_overview_day()
        sh = sh[[f_sha, f_shb, f_sh]]
        sh.columns = ['SHA', 'SHB', 'SH']

        sz = sz[f_sz]
        sz.name = 'SZ'

        cyb = cyb[f_cyb]
        cyb.name = 'CYB'

        zxqy = zxqy[f_zxqy]
        zxqy.name = 'ZXQY'

        szzb = szzb[f_szzb]
        szzb.name = 'SZZB'

        df = pd.concat([sh, sz, cyb, zxqy, szzb, ], axis=1)
        return df

    def get_pe(self):
        return self.get_overview_day_field('A_profitRate1', 'B_profitRate1', 'SH_profitRate1',
                                           '股票平均市盈率', '平均市盈率(倍)', '平均市盈率(倍)', '平均市盈率(倍)',)

    def get_market_val(self):
        return self.get_overview_day_field('A_marketValue1', 'B_marketValue1', 'SH_marketValue1',
                                           '股票总市值（元）', '上市公司市价总值(元)', '上市公司市价总值(元)', '上市公司市价总值(元)',)

    def get_negotiable_val(self):
        return self.get_overview_day_field('A_negotiableValue', 'B_negotiableValue', 'SH_negotiableValue',
                                           '股票流通市值（元）', '上市公司流通市值(元)', '上市公司流通市值(元)', '上市公司流通市值(元)',)

    def get_avg_price(self):
        sh, sz, cyb, zxqy, szzb = self.get_overview_day()

        sh_a = sh['A_trdAmt'].apply(float) * 10000 / sh['A_trdVol'].apply(float)
        sh_a.name = 'SHA'
        sh_b = sh['B_trdAmt'].apply(float) * 10000 / sh['B_trdVol'].apply(float)
        sh_b.name = 'SHB'
        sh_sh = sh['SH_trdAmt'].apply(float) * 10000 / sh['SH_trdVol'].apply(float)
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


class RZRQ:

    def _get_rzrq(self, code, index=False):

        def _fetch(code, index, page_num):
            s = None
            if not index:
                url = ('http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get?type=RZRQ_DETAIL_NJ&',
                       'token=70f12f2f4f091e459a279469fe49eca5&filter=(scode=%27[CODE]%27)&st=tdate&sr=-1&p=*****&'.replace(
                           '[CODE]', code),
                       'ps=50&js=var%20erHHrlfD={pages:(tp),data:(x)}&time=1&rt=50675219')
            else:
                if code == '000001':
                    url = ('http://dcfm.eastmoney.com//EM_MutiSvcExpandInterface/api/js/get?',
                           'token=70f12f2f4f091e459a279469fe49eca5&st=tdate&sr=-1&p=*****&ps=50&',
                           'js=var%20quzXmkEC={pages:(tp),data:%20(x)}&type=RZRQ_HSTOTAL_NJ&filter=(market=%27SH%27)&mk_time=1&rt=50706413')
                elif code == '399001':
                    url = ('http://dcfm.eastmoney.com//EM_MutiSvcExpandInterface/api/js/get?',
                           'token=70f12f2f4f091e459a279469fe49eca5&st=tdate&sr=-1&p=*****&ps=50&',
                           'js=var%20quzXmkEC={pages:(tp),data:%20(x)}&type=RZRQ_HSTOTAL_NJ&filter=(market=%27SZ%27)&mk_time=1&rt=50706413')

            while True:
                if s is None:
                    s = requests.Session()
                try:
                    url = ''.join(url).replace('*****', str(page_num))
                    r = s.get(url)
                    t = r.text[28:-1]
                    print(page_num, t[:50])

                    j = json.loads(t)
                    df = pd.DataFrame.from_dict(j)
                    break
                except Exception as e:
                    print(e.args)
                    print('sleep...')
                    time.sleep(60)
                    s = requests.Session()

            if not df.empty:
                df.index = pd.DatetimeIndex(df.tdate)
            return df

        def _fetch_dates(start, end, code, index):

            print(start, end, code, index)
            page_num = 1
            df = None
            dates = pd.date_range(start, end)
            if len(dates) == 0:
                return None

            while page_num <= 100:
                tmp = _fetch(code, index, page_num)
                if tmp.empty:
                    break

                if df is None:
                    df = tmp
                else:
                    df = pd.concat([df,  tmp])

                print(min(df.index), 'to', max(df.index))

                if min(df.index) <= min(dates) and max(df.index) >= max(dates):
                    break
                else:
                    time.sleep(1)

                page_num += 1

            return df

        def read_cache(code, index):
            if index:
                file_name = f'index_{code}.csv'
            else:
                file_name = f'{code}.csv'

            p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'rzrq' / f'{file_name}'
            if p.exists():
                df = pd.read_csv(str(p), index_col='date')
                df.index = pd.DatetimeIndex(df.index)
                return df
            return None

        def write_cache(df, code, index):
            if index:
                file_name = f'index_{code}.csv'
            else:
                file_name = f'{code}.csv'

            p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'rzrq' / f'{file_name}'
            df.to_csv(str(p), index_label='date')
        cache_df = read_cache(code, index)
        if cache_df is None:
            start = '1992-01-01'
        else:
            start = max(cache_df.index) + datetime.timedelta(days=0)

        new_df = _fetch_dates(start, datetime.datetime.now() - datetime.timedelta(days=3), code, index)
        if cache_df is not None:
            if new_df is not None:
                cache_df = cache_df.drop(new_df.index, errors='ignore')
            df = pd.concat([cache_df, new_df])
            len_cache = len(cache_df)

        else:
            df = new_df
            len_cache = 0

        df = df.sort_index()

        if len(df) > len_cache:
            write_cache(df, code, index)

        return df

    def get_rzrq(self, code, index=False):
        _cache_key = 'rzrq_%s' % code if not index else 'rzrq_index_%s' % code
        c = cache.get(_cache_key)
        if c is not None:
            return c
        rst = self._get_rzrq(code, index)
        cache.set(_cache_key, rst)
        return rst


class TDX:
    TDX_STOCK_DIR = settings.TDX_STOCK_DIR
    FQ_TYPE = 'qfq'

    def _get_df(self, code, index=False,  nrows=None):

        path = pathlib.Path(self.TDX_STOCK_DIR)
        path = path / self.FQ_TYPE
        if index:
            file_path = path / f'{code}.txt'
        else:
            file_path = path / f'SH#{code}.txt'

            if not file_path.exists():
                file_path = path / f'SZ#{code}.txt'

        if not file_path.exists():
            return None

        if not nrows:
            df = pd.read_csv(file_path, skipfooter=1, skiprows=1,
                             engine='python', encoding='gbk', sep='\t')
        else:
            df = pd.read_csv(file_path, skiprows=1, engine='python',
                             encoding='gbk', sep='\t', nrows=nrows)

        if index:
            df.drop(df.columns[6:], axis=1, inplace=True)
            df[6] = 0

        try:
            df.columns = ['date', 'open', 'high',
                          'low', 'close', 'volume', 'amount']
            df.index = pd.DatetimeIndex(df['date'])
            del df['date']
        except:
            if not nrows:
                raise
            return None

        return df

    def get_list(self, where='', sample=None, end=None):

        def filter_end(l):
            tmp = []
            for code in l:
                df = self._get_df(code, nrows=1)
                if df is None:
                    continue
                if df.empty:
                    continue
                if df.index[0] < pd.DatetimeIndex([end, ])[0]:
                    tmp.append(code)
            return tmp

        def filter_market_val(l):
            market_value = self.get_market_val().fillna(0).sort_values()[-1 * self.MARKET_SIZE:]
            tmp = []
            for code in l:
                if code in market_value.index:
                    tmp.append(code)
            return tmp

        path = pathlib.Path(self.TDX_STOCK_DIR) / 'qfq'

        _cache_key = '~'.join(['get_list', str(path), where, str(sample), str(end)])

        c = cache.get(_cache_key)
        if c is not None:
            return c

        rst = [f.name.split('#')[1].split('.')[0]
               for f in path.glob(f'{where}*.txt') if f.name.find('#') >= 0]

        if sample:
            return random.sample(rst, sample)

        if end:
            rst = filter_end(rst)

        print('处理数量：', len(rst))

        cache.set(_cache_key, rst)

        return rst

    def handler(self, sample=None):
        fields = ['open', 'high',
                          'low', 'close', 'volume', 'amount']
        p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'tdx'
        dfs = {}
        for field in fields:
            dfs[field] = pd.DataFrame(index=pd.date_range('19990101', datetime.datetime.now()))

        df = pd.DataFrame(data=pd.date_range('19990101', datetime.datetime.now()), columns=['date'])
        df.to_feather(p / self.FQ_TYPE / 'date_range')

        for code in self.get_list(sample=sample):
            tmp = self._get_df(code)

            for field in fields:
                dfs[field][code] = tmp[field]

        for field, df in dfs.items():
            df.reset_index(inplace=True)
            df.to_feather(p / self.FQ_TYPE / field)

    def get_fin(self, year, quarter):
        return get_fin(year, quarter)

class SD:
    TDX_STOCK_DIR = settings.TDX_STOCK_DIR
    FQ_TYPE = 'qfq'
    def __getitem__(self, feild):
        p = pathlib.Path(str(settings.APPS_DIR)) / 'datareader' / 'data' / 'tdx'
        return pd.read_feather(p / self.FQ_TYPE / field)

    def get_max_range2(self, code, start, end):
        '''
        跌幅
        '''
        df = self._get_df(code, start, end)

        if df is not None and not df.empty:
            max_high = max(df.high)
            max_high_idx = df.high.idxmax()
            min_low = min(df[df.index >= max_high_idx].low)

            return round(max_high / min_low, 1)
