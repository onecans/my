from . import leveldb_redis as backend


async def dumps(app, df, key):
    r = app['redis']
    db = app['leveldb']
    keys = await backend.dumps(df, key, db, r)
    return {'backend': 'redis', 'keys': keys}


async def loads_keys(app,  columns,  where=None, codes=None, to_df=False):
    r = app['redis']
    db = app['leveldb']
    if to_df:
        rst = await backend.loads_keys_as_df(db, r, columns, where, codes)
        return rst
    else:
        raise NotImplementedError


async def code_list(app, where):
    r = app['redis']
    db = app['leveldb']
    return await backend.code_list(where, r)


async def loads_base_info(app, columns):
    r = app['redis']
    db = app['leveldb']
    return await backend.loads_base_info(db, columns)
