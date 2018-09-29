import plyvel


async def init_leveldb(app):
    if 'leveldb' in app['config']:
        conf = app['config']['leveldb']
        app['leveldb'] = plyvel.DB(conf['name'],  create_if_missing=True)


async def close_leveldb(app):
    if 'leveldb' in app:
        app['leveldb'].close()
