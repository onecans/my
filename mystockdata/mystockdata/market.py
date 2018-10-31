import datetime
from collections import Counter

import pandas as pd
from click import progressbar

from mystockdata import db
from mystockdata.code_base import BaseInfoDb, CodeDb


class MarketDb(db.DatetimeIndexMixin, db.DfDb):
    prefix = 'market_'

    def __init__(self, where, **kwargs):
        super().__init__(**kwargs)
        self.db = self.db.prefixed_db(db.force_bytes(self.prefix+where))

    @classmethod
    def sh(cls):
        return cls(where='SH')

    @classmethod
    def sz(cls):
        return cls(where='SZ')

    @classmethod
    def all(cls):
        return cls(where='ALL')


def market_size(where="ALL"):
    df = BaseInfoDb().read(['sse', 'timeToMarket'])
    df = df[df['timeToMarket'] > 1990]
    df = df.assign(timeToMarket=df['timeToMarket'].apply(str)).\
        assign(cnt=1)
    if where == 'ALL':
        pass
    elif where == 'SH':
        df = df[df['sse'] == 'sh']
    elif where == 'SZ':
        df = df[df['sse'] == 'sh']
    else:
        raise ValueError('where can only be ALL, SH, SZ')

    df = df.groupby('timeToMarket').sum()
    df = df.cumsum()

    df.index = pd.DatetimeIndex(df.index)

    return df


def caculate():
    dates = pd.date_range('1990-01-01', datetime.datetime.now())
    # 计算market总市值,流通总市值
    df_sh = None
    df_sz = None
    sh_cnt = 0
    sz_cnt = 0
    cnt = 0

    dfs = {}
    for where in ('SH', 'SZ'):
        print('process', where)
        with progressbar(BaseInfoDb().stock_list(where)) as bar:
            for code in bar:

                try:
                    tmp = CodeDb(code).read(['bfq_close', 'bfq_low',
                                             'bfq_high', 'liquidity', 'shares',
                                             'is_min', 'is_max'
                                             ])
                except TypeError:
                    print(code)
                    continue

                pre = tmp.shift(1)
                tmp = tmp.assign(low_liquidity_amount=tmp['bfq_low'] * tmp['liquidity']).\
                    assign(high_liquidity_amount=tmp['bfq_high'] * tmp['liquidity']).\
                    assign(close_liquidity_amount=tmp['bfq_close'] * tmp['liquidity']).\
                    assign(low_shares_amount=tmp['bfq_low'] * tmp['shares']).\
                    assign(high_shares_amount=tmp['bfq_high'] * tmp['shares']).\
                    assign(close_shares_amount=tmp['bfq_close'] * tmp['shares']).\
                    assign(up=((tmp['bfq_close'] - pre['bfq_close'])) * 1 > 0)

                tmp = tmp.assign(
                    min_liquidity_amount=tmp['low_liquidity_amount']*tmp['is_min']).\
                    assign(
                        min_shares_amount=tmp['low_shares_amount']*tmp['is_min']).\
                    assign(
                    max_liquidity_amount=tmp['high_liquidity_amount']*tmp['is_max']).\
                    assign(
                        max_shares_amount=tmp['high_shares_amount']*tmp['is_max'])

                if where not in dfs:
                    dfs[where] = tmp.copy()
                else:
                    dfs[where] = dfs[where].add(tmp, fill_value=0)

        # cnts['x'] += 1
        # if cnts['x'] > 100:
        #     break

    dfs['ALL'] = dfs['SH'].add(dfs['SZ'], fill_value=0)

    print('caculate..')
    for where, df in dfs.items():
        m = market_size(where).reindex(df.index, method='ffill')
        df['market_size'] = m
        df['avg_close'] = df['bfq_close'] / df['market_size']
        df['avg_high'] = df['bfq_high'] / df['market_size']
        df['avg_low'] = df['bfq_low'] / df['market_size']
        df['up_profit'] = df['up'] / df['market_size']
        df['min_liquidity_profit'] = df['min_liquidity_amount'] / \
            df['low_liquidity_amount']
        df['min_shares_profit'] = df['min_shares_amount'] / \
            df['low_shares_amount']
        df['max_liquidity_profit'] = df['max_liquidity_amount'] / \
            df['high_liquidity_amount']
        df['max_shares_profit'] = df['max_shares_amount'] / \
            df['high_shares_amount']
        MarketDb(where).delete()
        MarketDb(where).save(df)
