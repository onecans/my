import yaml
from aiohttp import web


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    # TODO: add config validation
    return data


def redirect(request, name, **kw):
    router = request.app.router
    location = router[name].url(**kw)
    return web.HTTPFound(location=location)
