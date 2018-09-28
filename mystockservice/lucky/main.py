import asyncio
import logging
import pathlib
import sys

import click
from aiohttp import web

PROJ_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(PROJ_ROOT.absolute()))

try:
    from lucky.redis import close_redis, init_redis
    from lucky.utils import load_config

    from lucky.cache import init_cache

except:
    raise

# from aiohttp_security import setup as setup_security
# from aiohttp_security import CookiesIdentityPolicy


TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


async def init(loop):
    conf = load_config(PROJ_ROOT / 'config' / 'config.yml')

    app = web.Application(loop=loop)
    app.update(
        name='lucky',
        config=conf
    )
    # app.on_startup.append(init_mysql)
    app.on_startup.append(init_redis)
    app.on_startup.append(init_cache)
    # app.on_cleanup.append(close_mysql)
    app.on_cleanup.append(close_redis)

    # setup_security(app, CookiesIdentityPolicy(), AuthorizationPolicy(mongo))

    # setup views and routes
    from lucky.apps.k.routes import setup_routes
    setup_routes(app, PROJ_ROOT)

    return app


async def get_app():
    loop = asyncio.get_event_loop()
    return await init(loop)

gunicorn_app = get_app


@click.command()
@click.option('--host', default='127.0.0.1', help='Binding Host')
@click.option('--port', default='9001', help='Binding Port')
@click.option('--debug', default=False, help='Debug Flag')
def main(host, port, debug):
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(get_app())
    if debug:
        import aiohttp_debugtoolbar
        aiohttp_debugtoolbar.setup(app)
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
