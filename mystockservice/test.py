import os

from aiohttp import web

from aiohttp_cache import cache, setup_cache

DEBUG = bool(os.environ.get("DEBUG", False))


@cache(expires=5, unless=DEBUG)  # <-- Disable the Cache if we're in DEBUG mode
async def example_1(request):
    return web.Response(text="Example")


app = web.Application()

app.router.add_route('GET', "/", example_1)

setup_cache(app)

web.run_app(app, host="127.0.0.1")
