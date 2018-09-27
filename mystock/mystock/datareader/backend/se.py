
import json
import pathlib
import time

import pandas as pd
import requests

from .base import DfMixin


class SH_SE(DfMixin):
    file_path = '/data/stock/se'

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'sh_se'

    def down_load(self, dates):
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

        tmp = []
        for date in dates:
            tmp.append(_fetch(date))
            if len(dates) > 1:
                print('sleep')
                time.sleep(0.5)

        return pd.concat(tmp)


def _sz_down_load(dates, category):
    '''
    source: http://www.szse.cn/main/marketdata/tjsj/jbzb/
    '''
    def _sz_fetch(date, category):
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

    tmp = []
    if len(dates) == 1:
        return None
    for date in dates:
        tmp.append(_sz_fetch(date, category))
        if len(dates) > 1:
            print('sleep')
            time.sleep(0.5)

    return pd.concat(tmp)


class SZ_SE(DfMixin):
    file_path = '/data/stock/se'

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'sz_se'

    def down_load(self, dates):
        return _sz_down_load(dates, 'sz')


class SZZB_SE(DfMixin):
    file_path = '/data/stock/se'

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'szzb_se'

    def down_load(self, dates):
        return _sz_down_load(dates, 'szzb')


class ZXQY_SE(DfMixin):
    file_path = '/data/stock/se'

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'zxqy_se'

    def down_load(self, dates):
        return _sz_down_load(dates, 'zxqy')


class CYB_SE(DfMixin):
    file_path = '/data/stock/se'

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'cyb_se'

    def down_load(self, dates):
        return _sz_down_load(dates, 'cyb')


class SE:
    def __init__(self, *args, **kwargs):
        self.sz_se = SZ_SE()
        self.sz_df = self.sz_se.df()
        self.sh_se = SH_SE()
        self.sh_df = self.sh_se.df()
        self.szzb_se = SZZB_SE()
        self.szzb_df = self.szzb_se.df()
        self.zxqy_se = ZXQY_SE()
        self.zxqy_df = self.zxqy_se.df()
        self.cyb_se = CYB_SE()
        self.cyb_df = self.cyb_se.df()

    def refresh(self, days=5):
        for s in [self.sz_se, self.sh_se, self.szzb_se, self.zxqy_se, self.cyb_se]:
            s.del_n(days)

        self.__init__()

    def get_overview_day_field(self, f_sha, f_shb, f_sh, f_sz, f_cyb, f_zxqy, f_szzb):
        print(self.sh_df)
        sh = self.sh_df[[f_sha, f_shb, f_sh]]
        sh.columns = ['SHA', 'SHB', 'SH']

        sz = self.sz_df[f_sz]
        sz.name = 'SZ'

        cyb = self.cyb_df[f_cyb]
        cyb.name = 'CYB'

        zxqy = self.zxqy_df[f_zxqy]
        zxqy.name = 'ZXQY'

        szzb = self.szzb_df[f_szzb]
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
        sh, sz, cyb, zxqy, szzb = self.sh_se, self.sz_se, self.cyb_se, self.zxqy_se, self.szzb_se

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
