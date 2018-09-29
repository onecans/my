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


async def series_to_db(db, key, series, as_df=True):
    # return
    if isinstance(series, pd.DatetimeIndex):
        series = series.strftime('%Y-%m-%d')

    if as_df:
        print('put', key.encode())
        db.put(key.encode(), zlib.compress(pickle.dumps(series)))
    else:
        raise NotImplementedError


async def db_to_series(db, key, to_df=True):
    if to_df:
        print('get', key.encode())
        return pickle.loads(zlib.decompress(db.get(key.encode())))
    else:
        raise NotImplementedError


async def df_to_db(db, key, df):
    keys = []
    with db.write_batch() as wb:
        for column in df.columns:
            _key = column_key(key, column)
            keys.append(_key)
            # print('put', _key)
            db.put(_key.encode(), zlib.compress(pickle.dumps(df[column])))
        _key = index_key(key)
        # print('put', _key)
        keys.append(_key)
        db.put(_key.encode(), zlib.compress(pickle.dumps(df.index)))

    return keys


async def db_delete_df(db, key, df):
    with db.write_batch() as wb:
        for column in df.columns:
            _key = column_key(key, column)
            # print('delete', _key)
            db.delete(_key.encode())
        _key = index_key(key)
        # print('delete', _key)
        db.delete(_key.encode())


async def db_delete(db, key):
    # print('delete', key)
    db.delete(key.encode())


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


async def dumps(df, key, db, redis):
    await db_delete_df(db, key, df)
    keys = await df_to_db(db, key, df)

    # keys = [f'{key}__{column}' for column in df.columns]
    # keys.append(f'{key}__index')
    # for _key in keys:
    #     await db_delete(db, _key)

    # for column in df.columns:
    #     await series_to_db(db, column_key(key, column), df[column])

    # await series_to_db(db, index_key(key), df.index)

    # await db.execute('SET', f'{key}_columns', df.to_json(orient='columns'))
    # await db.execute('HSET', 'SH')
    where, code = parse_file_name(key)
    # print("HSET", where, code, key)
    await redis.execute('HSET', where, code, key)
    if where in ('SH', 'SZ'):
        await redis.execute('HSET', 'ALL', code, key)
    return keys


async def loads_keys_as_df(db, redis, columns,  where=None, codes=None):
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
            tmp = await db_to_series(db, real_key, to_df=True)
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


async def loads_base_info(db, columns):
    if not 'index' in columns:
        columns.append('index')

    key = 'base_info'

    data = dict()

    for column in columns:
        real_key = column_key(key, column)
        tmp = await db_to_series(db, real_key, to_df=True)
        data[column] = tmp

    df = pd.DataFrame(data={key: value for key, value in data.items(
    ) if key != 'index'}, index=data['index'])
    return df
