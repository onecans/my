from aiohttp_cache import RedisConfig, setup_cache


async def init_cache(app):
    conf = app['config']['cache']
    redis_config = RedisConfig(host=conf['host'],
                               port=conf['port'],
                               db=conf['db'],
                               password=conf['password'],
                               key_prefix=conf['key_prefix'])
    await setup_cache(app, cache_type="redis", backend_config=redis_config)
