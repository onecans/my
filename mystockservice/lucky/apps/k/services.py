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
from lucky.apps import backends
from lucky.base.parameter import build_parameters, fetch_parameters

from . import services
from .utils import chunk

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
    df = await backends.code_info(paras.app, paras.code, [paras.col, ], )
    tmp = {}
    if not df.empty:
        df = _filter_df(df, paras)

    return df


async def loads_base_info(paras):
    df = await backends.loads_base_info(paras.app, paras.col.split(','), paras.code.split(','))

    return df.to_dict()


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


async def se_info(app, column, category=None):
    df = await backends.se_info(app, column, category)
    print(df.index)
    df.index = df.index.strftime('%Y-%m-%d')
    return df.to_dict()


async def market_info(app, columns, start, end, where='ALL'):
    df = await backends.market_info(app, columns, where)
    if start and start != 'start':
        df = df[df.index >= start]
    if end and end != 'end':
        df = df[df.index <= end]
    return round(df, 6)

# async def k_min_max_counter(paras):
#     window_size = int(paras.query.get('window_size', 52*7))
#     resample = paras.query.get('resample', '')
#     df = await _line(paras)
#     df = pd.DataFrame(df)
#     col = paras.col
#     df['cummax'] = df.cummax()
#     df['cummin'] = df[col].cummin()
#     df['ismin'] = df[col] == df['cummin']
#     df['ismax'] = df[col] == df['cummax']

#     df['rolling_max'] = df[col].rolling(window_size).max()
#     df['rolling_min'] = df[col].rolling(window_size).min()
#     df['is_rolling_max'] = df[col] == df['rolling_max']
#     df['is_rolling_min'] = df[col] == df['rolling_min']

#     counters = {}
#     for _col in ['is_rolling_max', 'is_rolling_min', 'ismin', 'ismax']:
#         tmp = df[[_col]]
#         if resample:
#             tmp = tmp.resample(resample).sum()
#             tmp = tmp > 0

#         tmp = tmp[tmp.sum(axis=1) > 0]
#         tmp.index = tmp.index.strftime('%Y-%m-%d')
#         c = Counter()
#         c.update(**tmp.to_dict()[_col])
#         counters[_col] = c

#     return counters
