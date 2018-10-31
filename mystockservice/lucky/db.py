from aiomysql import create_engine


async def init_mysql(app):
    conf = app['config']['mysql']
    engine = await create_engine(
        db=conf['db'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine


async def close_mysql(app):
    app['db'].close()
    await app['db'].wait_closed()
