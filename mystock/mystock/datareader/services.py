import asyncio
import json
import math
import sys
from pprint import pprint

import aiohttp
import async_timeout
import click
import pandas as pd
import requests
from django.conf import settings


def get_server():
    stock_server = settings.STOCKSERVER
    if stock_server.endswith('/'):
        stock_server = stock_server[:-1]
    return stock_server


def line(code, start, end, col):
    stock_server = get_server()
    query = {}
    line_url = '{stock_server}/code_info/{start}/{end}/{code}'.format(**locals())
    if col:
        query['col'] = col
    print(line_url, query)
    tmp = requests.get(line_url, params=query).json()['result']
    return tmp


def se(col, category):
    stock_server = get_server()
    url = '{stock_server}/se/info'.format(**locals())
    query = {}
    query['col'] = col
    if category:
        query['category'] = category
    print(url, query)
    tmp = requests.get(url, params=query).json()['result']
    return tmp


def baseinfo(code, col):
    stock_server = get_server()
    query = {}
    url = '{stock_server}/baseinfo/{code}'.format(**locals())
    query['col'] = col
    tmp = requests.get(url, params=query).json()['result']
    rst = {}
    for key, value in tmp.items():
        rst[key] = value[code]

    return rst


def code_str(code):
    try:
        v = baseinfo(code, 'name')
        return '%s-%s' % (code, v['name'])
    except:
        return code


class AioHttpFetch():

    def __init__(self, *args, **kwargs):
        self.stock_server = get_server()

    async def do_fetch(self, session, url):
        async with async_timeout.timeout(1000):
            async with session.get(url) as response:
                return await response.json()

    async def get_codes(self, where="ALL", min_timetomarket=None):
        # return ['601600']
        async with aiohttp.ClientSession() as session:
            if min_timetomarket:
                codes = await self.do_fetch(session, '{self.stock_server}/se/codelist/{where}?start_timetomarket={min_timetomarket}'.format(**locals()))
            else:
                codes = await self.do_fetch(session, '{self.stock_server}/se/codelist/{where}'.format(**locals()))
            return codes['result']

    async def get_marketsize(self, where="ALL",):
        async with aiohttp.ClientSession() as session:
            marketsize = await self.do_fetch(session, '{self.stock_server}/se/size?where={where}'.format(**locals()))

            return marketsize['result']

    def x_get_marketsize(self, where='ALL'):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rst = loop.run_until_complete(self.get_marketsize(where))
        loop.close()
        return rst

    async def _fetch(self, url,  **kwargs):
        min_timetomarket = kwargs.pop('min_timetomarket', None)
        where = kwargs.pop('where', 'ALL')
        limit = kwargs.pop('limit', 20)
        conn = aiohttp.TCPConnector(limit=limit)
        codes = await self.get_codes(min_timetomarket=min_timetomarket, where=where)
        session = aiohttp.ClientSession(connector=conn)
        test = kwargs.pop('test', False)
        if url.startswith('/'):
            url = self.stock_server + url
        if test:
            _codes = codes[:100]
        else:
            _codes = codes
        jobs = [self.do_fetch(session, url.format(code=code, **kwargs))
                for code in _codes]
        rsts = []
        for next_ in asyncio.as_completed(jobs):
            try:
                r = await next_
                if r['result']:
                    rsts.append(r)
            except:
                print('Error')

        await session.close()
        self.rsts = rsts
        # return rsts

    def x_fetch(self, url, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # loop = asyncio.get_event_loop()
        loop.run_until_complete(self._fetch(url, **kwargs))
        loop.close()
        return self.rsts
