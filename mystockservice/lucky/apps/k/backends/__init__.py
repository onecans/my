from . import redis


async def dumps(app, df, key):
    r = app['redis']
    keys = await redis.dumps(df, key, r)
    return {'backend': 'redis', 'keys': keys}


async def loads_keys(app,  columns,  where=None, codes=None, to_df=False):
    r = app['redis']

    if to_df:
        rst = await redis.loads_keys_as_df(r, columns, where, codes)
        return rst
    else:
        raise NotImplementedError


async def code_list(app, where):
    r = app['redis']
    return await redis.code_list(where, r)


async def loads_base_info(app, columns):
    r = app['redis']
    return await redis.loads_base_info(r, columns)
