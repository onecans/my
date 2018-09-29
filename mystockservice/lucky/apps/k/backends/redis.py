import itertools
import pickle
import zlib
from collections import Iterable, OrderedDict, defaultdict

import pandas as pd

from lucky.apps.k.utils import *


def force_decode(f):
    async def warp(*args, **kwargs):
        rst = await f(*args, **kwargs)
        if hasattr(rst, 'decode'):
            return rst.decode()
        if isinstance(rst, dict):
            return {key: value.decode() for key, value in rst.items()}
        if isinstance(rst, list):
            return [x.decode() for x in rst]
        return rst
    return warp


async def series_to_redis(redis, key, series, as_df=True):
    if isinstance(series, pd.DatetimeIndex):
        series = series.strftime('%Y-%m-%d')

    if as_df:
        await redis.execute('SET', key, zlib.compress(pickle.dumps(series)))
    else:
        await redis.execute('RPUSH', key, *series)


async def redis_to_series(redis, key, to_df=True):

    if to_df:
        return pickle.loads(zlib.decompress(await redis.get(key)))
    else:
        return await redis.execute('LRANGE', real_key, 0, -1)


def index_key(key):
    try:
        return f'{key.decode()}__index'
    except AttributeError:
        return f'{key}__index'


def column_key(key, column):
    try:
        return f'{key.decode()}__{column}'
    except AttributeError:
        return f'{key}__{column}'


async def dumps(df, key, redis):
    keys = [f'{key}__{column}' for column in df.columns]
    keys.append(f'{key}__index')
    await redis.execute('DEL', *keys)

    for column in df.columns:
        await series_to_redis(redis, column_key(key, column), df[column])

    await series_to_redis(redis, index_key(key), df.index)

    # await redis.execute('SET', f'{key}_columns', df.to_json(orient='columns'))
    # await redis.execute('HSET', 'SH')
    where, code = parse_file_name(key)
    # print("HSET", where, code, key)
    await redis.execute('HSET', where, code, key)
    if where in ('SH', 'SZ'):
        await redis.execute('HSET', 'ALL', code, key)
    return keys


# def handler(df):
#     def func(c):
#         try:
#             return df[c].apply(float)
#         except:
#             return df[c].apply(bytes.decode)
#     t = {}
#     for c in df.columns:
#         t[c] = func(c)

#     df = df.assign(**t)
#     try:
#         df.index = pd.DatetimeIndex(df.index.map(bytes.decode))
#     except Exception as e:
#         pass
#     return df


async def loads_keys_as_df(redis, columns,  where=None, codes=None):
    if not 'index' in columns:
        columns.append('index')
    if codes:
        real_keys = await redis.execute('HMGET', where, *codes)

        real_keys = {code: real_key for code,
                     real_key in zip(codes, real_keys)}
    else:
        real_keys = await redis.execute('HGETALL', where)
    real_keys = OrderedDict(real_keys)
    # print(real_keys)
    # if not to_df:
    data = defaultdict(dict)
    # else:
    #     data = defaultdict(pd.DataFrame)

    for code, key in real_keys.items():
        for column in columns:
            real_key = column_key(key, column)
            tmp = await redis_to_series(redis, real_key, to_df=True)
            data[code][column] = tmp
            # try:
            #     data[code][column] = data[code][column].apply(float)
            # except:
            #     data[code][column] = data[code][column].apply(bytes.decode)
        # try:
        #     data[code].index = pd.DatetimeIndex(
        #         data[code]['index'])
        # except:
        #     data[code].index = data[code]['index']
        # finally:
        #     del data[code]['index']
    import time
    s = time.time()
    dfs = []
    for code, col_values in data.items():

        df = pd.DataFrame(data={key: value for key, value in col_values.items(
        ) if key != 'index'}, index=col_values['index'])
        df['code'] = code

        dfs.append(df)

    df = pd.concat(dfs)
    e = time.time()
    print('use ', e-s)
    # df = handler(df)
    try:
        df.index = pd.DatetimeIndex(df.index)
    except Exception as e:
        pass
    return df


@force_decode
async def code_list(where, redis):
    return await redis.execute('HKEYS', where)


async def key_map(redis, where='ALL'):
    x = await redis.hgetall(where)


async def loads_base_info(redis, columns):
    if not 'index' in columns:
        columns.append('index')

    key = 'base_info'

    data = dict()

    for column in columns:
        real_key = column_key(key, column)
        tmp = await redis_to_series(redis, real_key, to_df=True)
        data[column] = tmp

    df = pd.DataFrame(data={key: value for key, value in data.items(
    ) if key != 'index'}, index=data['index'])
    return df
