import aioredis

_redis_pool = None


def redis_pool():
    if not _redis_pool:
        raise Exception('InitError')
    else:
        return _redis_pool


async def init_redis(app):
    global _redis_pool
    if 'redis' in app['config']:
        conf = app['config']['redis']
        _redis_pool = await aioredis.create_redis_pool(
            conf['redis_url'],
            minsize=conf['minsize'], maxsize=conf['maxsize']
            # , encoding='utf8'
        )
        app['redis'] = _redis_pool


async def close_redis(app):
    if 'redis' in app:
        app['redis'].close()
        await app['redis'].wait_closed()
