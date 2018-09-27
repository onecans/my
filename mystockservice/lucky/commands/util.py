import asyncio
import math
import sys
from pprint import pprint

import aiohttp
import async_timeout
import click
import pandas as pd

HOST = 'http://127.0.0.1:9001'

URL = HOST + '/k/min/{start}/{end}/{code}?k={k}'


async def do_fetch(session, url):
    async with async_timeout.timeout(1000):
        async with session.get(url) as response:
            return await response.json()


async def get_codes(where="ALL", min_timetomarket=None):
    # return ['601600']
    async with aiohttp.ClientSession() as session:
        if min_timetomarket:
            codes = await do_fetch(session, f'{HOST}/k/codes/{where}?start_timetomarket={min_timetomarket}')
        else:
            codes = await do_fetch(session, f'{HOST}/k/codes/{where}')
        return codes['result']


async def get_marketsize(where="ALL",):
    async with aiohttp.ClientSession() as session:
        marketsize = await do_fetch(session, f'{HOST}/k/marketsize?where={where}')
        print(marketsize)
        return marketsize['result']


async def fetch(url,  **kwargs):
    min_timetomarket = kwargs.pop('min_timetomarket', None)
    where = kwargs.pop('where', 'ALL')
    limit = kwargs.pop('limit', 20)
    conn = aiohttp.TCPConnector(limit=limit)
    codes = await get_codes(min_timetomarket=min_timetomarket, where=where)
    session = aiohttp.ClientSession(connector=conn)
    test = kwargs.pop('test', False)
    if url.startswith('/'):
        url = HOST + url
    if test:
        _codes = codes[:100]
    else:
        _codes = codes
    jobs = [do_fetch(session, url.format(code=code, **kwargs))
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

    return rsts


def render(chart, path='render.html'):
    chart.height = 600
    chart.width = 1200
    chart._option['dataZoom'] = [{'show': True, 'type': 'slider', 'start': 0,
                                  'end': 100, 'orient': 'horizontal', 'xAxisIndex': None, 'yAxisIndex': None}]
    chart._option['tooltip']['axisPointer'] = {'animation': False,
                                               'type': "cross",
                                               'crossStyle': {
                                                   'color': "#376DF4"
                                               }}

    chart.render(path=path)
