import asyncio
import math
import sys
from pprint import pprint

import aiohttp
import async_timeout
import click
import pandas as pd

URL = 'http://127.0.0.1:9001/k/min/{start}/{end}/{code}?k={k}'


async def do_fetch(session, url):
    async with async_timeout.timeout(1000):
        async with session.get(url) as response:
            return await response.json()


async def get_codes(where="ALL", min_timetomarket=None):

    async with aiohttp.ClientSession() as session:
        if min_timetomarket:
            codes = await do_fetch(session, 'http://127.0.0.1:9001/k/codes/{where}?start_timetomarket={min_timetomarket}'.format(**locals()))
        else:
            codes = await do_fetch(session, 'http://127.0.0.1:9001/k/codes/{where}'.format(**locals()))
        return codes['result']


async def fetch(start, end, k=90, codes=None, min_timetomarket=None):
    conn = aiohttp.TCPConnector(limit=20)
    if codes is None:
        codes = await get_codes(min_timetomarket=min_timetomarket)
    session = aiohttp.ClientSession(connector=conn)
    jobs = [do_fetch(session, URL.format(start=start, end=end, code=code, k=k))
            for code in codes]
    rsts = []
    for next_ in asyncio.as_completed(jobs):
        try:
            r = await next_
            if r['result']:
                rsts.append((r['paras']['code'], r['result']))
        except:
            print('Error')

    await session.close()

    return rsts


async def process(file_name, start, end, k=90, min_timetomarket=None):
    rsts = await fetch(start, end,  k, min_timetomarket=min_timetomarket)
    # print(rsts)
    # if file_name:
    #     df.to_excel(file_name)
    # else:
    #     print(df)
    print([r[0] for r in rsts])
    for r in rsts:
        print(r[0])
    cnt = len(rsts)
    print('共{cnt}只股票'.format(**locals()))


@click.command()
@click.option('--start', default='1992-01-01', help='start')
@click.option('--end', default='2018-09-30', help='end')
@click.option('--last_days', default=90, help='last_days')
@click.option('--file_name', default='', help='file_name')
@click.option('--min_timetomarket', default=20180101, help='用于去除近期上市的股票')
def main(start, end,  last_days, file_name, min_timetomarket):
    """
    近{last_days}破新低的股票列表
    """
    print('='*50)
    print('近{last_days}天，从{start}至{end} 破新低的股票列表:'.format(**locals()))
    import time
    b = time.time()
    loop = asyncio.get_event_loop()
    if not file_name.endswith('.xlsx'):
        file_name = file_name + '.xlsx'
    loop.run_until_complete(
        process(file_name, start, end, last_days, min_timetomarket))
    e = time.time()
    print(e-b)


if __name__ == '__main__':
    main()
