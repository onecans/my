import asyncio
import datetime
import json
import math
import os
import pathlib
import time
from collections import Counter, defaultdict, namedtuple
from concurrent.futures import ProcessPoolExecutor
from json import JSONEncoder

import aioredis
import numpy as np
import pandas as pd
from aiohttp import web

from aiohttp_cache import cache
from lucky.base.parameter import build_parameters, fetch_parameters

from . import backends, services
from .utils import chunk, parse_file_name

code_list = backends.code_list


def _desc(df, col):
    if df.empty:
        return []
    desc = df.groupby('code').describe(
        percentiles=[.01, .05, .1, .25, .5, .75]).to_dict()
    tmp = defaultdict(dict)

    for key, value in desc.items():
        for code, real_value in value.items():
            tmp[code][key[1]] = real_value

    try:
        idxmin = df.groupby('code').idxmin().to_dict()[col]
        idxmax = df.groupby('code').idxmax().to_dict()[col]
    except:
        df[col] = pd.to_numeric(df[col])

        idxmin = df.groupby('code').idxmin().to_dict()[col]
        idxmax = df.groupby('code').idxmax().to_dict()[col]
    for code, value in idxmin.items():
        tmp[code]['idxmin'] = value.strftime(
            '%Y-%m-%d')
    for code, value in idxmax.items():
        tmp[code]['idxmax'] = value.strftime(
            '%Y-%m-%d')

    for code, value in tmp.items():
        value['code'] = code
        value['col'] = col

    tmp = list(tmp.values())

    return tmp


def _filter_df(df, paras):
    if paras.start and paras.start != 'start':
        df = df[df.index >= paras.start]
    if paras.end and paras.end != 'end':
        df = df[df.index <= paras.end]
    return df


async def _to_df(paras):
    codes = paras.code.split(',')
    df = await backends.loads_keys(paras.app, [paras.col, ], codes=codes, where=paras.where, to_df=True)
    tmp = {}
    if not df.empty:
        df = _filter_df(df, paras)

    return df


async def describe(paras):
    codes = [paras.code, ]
    df = await backends.loads_keys(paras.app, [paras.col, ], codes=codes, where='ALL', to_df=True)
    tmp = {}
    if not df.empty:
        df = _filter_df(df, paras)
        tmp = _desc(df, paras.col)
    # rst = {'start': paras.start, 'end': paras.end, 'datetime': datetime.datetime.now().isoformat(),
    #        'hits': tmp}
    return tmp


async def describe_all(paras):

    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor(max_workers=8)
    if paras.code == 'ALL':
        codes = await backends.code_list(paras.app, paras.where)
    else:
        codes = paras.code.split(',')
    records = []
    jobs = []
    for idx, l in enumerate(chunk(codes, 100)):
        jobs.append(loads_keys(
            paras.app, [paras.col, ], codes=l, where=paras.where, to_df=True))

    for _next in asyncio.as_completed(jobs):
        df = await(_next)

        if df.empty:
            continue

        if paras.start and paras.start != 'start':
            df = df[df.index >= paras.start]

        if paras.end and paras.end != 'end':
            df = df[df.index <= paras.end]

        tmp = executor.submit(_desc, df, paras.col)
        # tmp = _desc(df, col)
        records.append(tmp)
    executor.shutdown(wait=True)
    tmp = []
    for rec in records:
        tmp.extend(rec.result())

    rst = {'start': paras.start, 'end': paras.end, 'datetime': datetime.datetime.now().isoformat(),
           'hits': tmp}
    return rst


async def post_file(app, file_name, index=False, columns=['date', 'open', 'high',
                                                          'low', 'close', 'volume', 'amount']):
    k_file_path = app['config']['k_file_path']
    bfq_k_file_path = app['config']['bfq_k_file_path']
    xdxr_file_path = app['config']['xdxr_file_path']
    
    tmp = pd.read_csv(os.path.join(k_file_path, file_name), skiprows=1, engine='python',
                      encoding='gbk', sep='\t', skipfooter=1)
    if index:
        tmp.drop(tmp.columns[6:], axis=1, inplace=True)
        tmp[6] = 0
    if not columns:
        raise web.HTTPInternalServerError()
    tmp.columns = columns
    if 'date' in tmp.columns:
        tmp.index = pd.DatetimeIndex(tmp['date'])
        del tmp['date']
    dates = pd.date_range(min(tmp.index),max(tmp.index))
    # 处理bfq
    if not index and pathlib.Path(os.path.join(bfq_k_file_path, file_name)).exists():
        
        bfq = pd.read_csv(os.path.join(bfq_k_file_path, file_name), skiprows=1, engine='python', encoding='gbk', sep='\t', skipfooter=1)
        bfq.columns = ['bfq_' + c for c in columns]
        if 'bfq_date' in bfq.columns:
            bfq.index = pd.DatetimeIndex(bfq['bfq_date'])
            del bfq['bfq_date']
            del bfq['bfq_volume']
            del bfq['bfq_amount']
    
        tmp = pd.concat([tmp, bfq], axis=1, join='inner').reindex(dates, method='ffill')
        
    
    # 处理xdxr
    _,code= parse_file_name(file_name)
    xdxr_file_path = xdxr_file_path + code + '.csv'
    # print(xdxr_file_path)
    if pathlib.Path(xdxr_file_path).exists():
        
        xdxr = pd.read_csv(xdxr_file_path)
        xdxr.index = pd.DatetimeIndex(xdxr.date)

        xdxr = xdxr[xdxr['category'] != 6] # 去除 6-增发新股

        df1 = xdxr[['shares_before']].dropna()
        df2 = xdxr[['shares_after']].dropna()
        df3 = xdxr[['liquidity_before']].dropna()
        df4 = xdxr[['liquidity_after']].dropna()

        if sum(df1.index.duplicated(keep=False)):
            df1 = df1.groupby(df1.index).min()

        if sum(df2.index.duplicated(keep=False)):
            df2 = df2.groupby(df2.index).max()

        if sum(df3.index.duplicated(keep=False)):
            df3 = df3.groupby(df3.index).min()

        if sum(df4.index.duplicated(keep=False)):
            df4 = df4.groupby(df4.index).max()

        # print(df4)
        df1 = df1.reindex(dates, method='bfill')
        df2 = df2.reindex(dates, method='ffill')
        df3 = df3.reindex(dates, method='bfill')
        df4 = df4.reindex(dates, method='ffill')


        xdxr = pd.concat([df1,df2, df3,df4],axis=1).fillna(0)

        xdxr['shares'] = xdxr[['shares_before','shares_after']].apply(max,axis=1)
        xdxr['liquidity'] = xdxr[['liquidity_before','liquidity_after']].apply(max,axis=1)

        xdxr = xdxr[['shares','liquidity']]
        
        tmp = pd.concat([tmp,xdxr],axis=1)
        tmp = tmp.sort_index()
    else:
        print(code, 'not found xdxr')
    # print(tmp)
    # print(tmp)
    rst = await backends.dumps(app, tmp, file_name)
    return rst


async def post_base_info(app):
    import tushare as ts
    df = ts.get_stock_basics()
    rst = await backends.dumps(app, df, 'base_info')
    return rst


async def loads_base_info(paras):
    df = await backends.loads_base_info(paras.app, paras.col.split(','))

    df = df[df.index.isin(paras.code.split(','))]

    return df.to_dict()


def _topk(df, col,  ascending=True, k=10):
    df = df.sort_values(col, ascending=ascending)[:k][col]
    tmp = df.to_dict()

    tmp = {k.strftime('%Y-%m-%d'): v for k, v in tmp.items()}
    if len(tmp.values()) > 0:
        tmp['mean'] = round(sum(tmp.values()) / len(tmp.values()), 4)

    return tmp


async def volume(paras):
    df = await _to_df(paras)
    total = await loads_base_info(build_parameters(paras=paras, col='totals'))
    _total = total['totals'][paras.code]
    if 'use_hs' in paras.query:
        df['volume'] = round((df['volume'] * 100) / (_total * 100000000), 4)
    desc = _desc(df, 'volume')
    for d in desc:
        d['totals'] = total['totals'][d['code']]
    k = int(paras.query.get('k', 3))
    min10 = _topk(df, 'volume', ascending=True, k=k)
    top10 = _topk(df, 'volume', ascending=False, k=k)
    rst = dict(desc=desc, mink=min10, topk=top10)

    return rst


async def _line(paras):
    try:
        df = await _to_df(paras)

        df = df.dropna(how='all')

        start = paras.start if paras.start != 'start' else min(df.index)
        end = paras.end if paras.end != 'end' else max(df.index)
        print(start, end)
        ds = pd.date_range(start, end)
        df = df.reindex(ds, method='bfill',
                        copy=False, fill_value=np.NaN)

        return df[paras.col]
    except:
        print(paras)
        raise


async def line(paras):
    df = await _line(paras)
    df.index = df.index.strftime('%Y-%m-%d')
    return df.to_dict()


async def k_min(paras):
    df = await _line(paras)
    min_date = df.idxmin()
    k = int(paras.query.get('k', 90))
    df = df.tail(n=k)
    if min_date in df.index:
        return True
    else:
        return False


async def k_max(paras):
    df = await _line(paras)
    min_date = df.idxmax()
    k = int(paras.query.get('k', 90))
    df = df.tail(n=k)
    if min_date in df.index:
        return True
    else:
        return False


async def k_min_max_counter(paras):
    window_size = int(paras.query.get('window_size', 52*7))
    resample = paras.query.get('resample', '')
    df = await _line(paras)
    df = pd.DataFrame(df)
    col = paras.col
    df['cummax'] = df.cummax()
    df['cummin'] = df[col].cummin()
    df['ismin'] = df[col] == df['cummin']
    df['ismax'] = df[col] == df['cummax']

    df['rolling_max'] = df[col].rolling(window_size).max()
    df['rolling_min'] = df[col].rolling(window_size).min()
    df['is_rolling_max'] = df[col] == df['rolling_max']
    df['is_rolling_min'] = df[col] == df['rolling_min']

    counters = {}
    for _col in ['is_rolling_max', 'is_rolling_min', 'ismin', 'ismax']:
        tmp = df[[_col]]
        if resample:
            tmp = tmp.resample(resample).sum()
            tmp = tmp > 0

        tmp = tmp[tmp.sum(axis=1) > 0]
        tmp.index = tmp.index.strftime('%Y-%m-%d')
        c = Counter()
        c.update(**tmp.to_dict()[_col])
        counters[_col] = c

    return counters


async def k_marketsize(paras):
    df = await backends.loads_base_info(paras.app, ['timeToMarket'])
    df = df[df['timeToMarket'] > 1990]

    if 'where' in paras.query:
        codes = await backends.code_list(paras.app, paras.query['where'])
        df = df[df.index.isin(codes)]
    df['timeToMarket'] = df['timeToMarket'].apply(str)
    df['cnt'] = 1
    df = df.groupby('timeToMarket').sum()
    df = df.cumsum()
    df.index = pd.DatetimeIndex(df.index)
    df = df.reindex(pd.date_range(min(df.index),
                                  datetime.datetime.now()), method='ffill')
    # df = df.resample('1d').ffill()
    df.index = df.index.strftime('%Y-%m-%d')
    return df.to_dict()
