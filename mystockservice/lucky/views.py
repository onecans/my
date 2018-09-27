import json
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from aiohttp import web

Body = namedtuple('Body', 'cmd userid pwd seqid rpts')
Message = namedtuple(
    'Message', 'date out_msg_id msg_id phone channel extnum \
    channel_status rpt_status attr1 attr2 attr3 attr4 attr5')


class Sp(metaclass=ABCMeta):
    def __init__(self, name, app):
        self.name = name
        self.app = app
        self.es_type = app['config']['es_type']
        self.es_redis_key = app['config']['es_redis_key']

    @abstractmethod
    def response_body(self, *args, **kwargs):
        pass

    @abstractmethod
    def validate_body(self, body):
        pass

    @abstractmethod
    def parse(self, *args, **kwargs):
        pass

    async def handler(self, body):
        def _add_fields(rec):
            rec['sp_name'] = self.name
            rec['type'] = self.es_type
            return rec

        self.validate_body(body)
        msgs = self.parse(body)
        success = True
        # TODO mysql

        # TODO redis
        redis = self.app['redis']

        await redis.execute('LPUSH', self.es_redis_key,
                            *[json.dumps(_add_fields(msg._asdict()))
                              for msg in msgs])

        response_body = self.response_body(body, success)
        return web.Response(body=response_body)


class Mw(Sp):
    def __init__(self, app):
        super().__init__(app=app, name='MW', )

    def response_body(self, body, success):
        body = 'cmd=RPT_RESP&seqid=%s&ret=%s' % (
            body.seqid, 0 if success else 1)
        return body

    def validate_body(self, body):
        if body.cmd != 'RPT_REQ':
            raise web.HTTPForbidden()

    def parse(self, body):
        msgs = []
        for rpt in body.rpts.split(','):
            msg = Message(*rpt.split('|'))
            msgs.append(msg)
        return msgs


async def mw(request):
    data = await request.post()
    body = Body(**data)
    handler = Mw(request.app)
    resp = await handler.handler(body)
    return resp


async def test(request):
    return web.Response(body='x')
