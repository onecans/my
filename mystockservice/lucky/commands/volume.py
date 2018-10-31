import asyncio
import math
import sys
from pprint import pprint

import aiohttp
import async_timeout
import click
import pandas as pd

# URL = 'http://127.0.0.1:9001/k/volume/2015-06-15/end/{code}?nocache&use_hs'
# URL = 'http://127.0.0.1:9001/k/volume/2015-06-15/end/{code}?&use_hs'
URL = 'http://127.0.0.1:9001/k/volume/{start}/{end}/{code}?k={k}'


async def fetch(session, url):
    async with async_timeout.timeout(1000):
        async with session.get(url) as response:
            return await response.json()


async def get_codes():

    async with aiohttp.ClientSession() as session:
        codes = await fetch(session, 'http://127.0.0.1:9001/k/codes/SH')
        # html = await fetch(session, 'http://python.org')
        # return ['601600', '601601']
        return codes['result']


async def fetch_volume(start, end, k=10, codes=None):
    conn = aiohttp.TCPConnector(limit=20)
    if codes is None:
        codes = await get_codes()
    session = aiohttp.ClientSession(connector=conn)
    jobs = [fetch(session, URL.format(start=start, end=end, code=code, k=k))
            for code in codes]
    rsts = []
    for next_ in asyncio.as_completed(jobs):
        try:
            r = await next_
            rsts.append(r['result'])
        except:
            print('Error')

    await session.close()

    return rsts


async def get_both_min_codes(codes):
    rsts0 = await fetch_volume('2015-06-15', end2, k=30, codes=codes)
    new_codes = []
    for rec in rsts0:
        if len(rec['desc']) == 0:
            continue
        tmp = rec['desc'][0]
        min10 = rec['mink']

        has_1 = False
        has_2 = False
        for key in min10.keys():
            if key >= '2018-02-01':
                has_1 = True

            if '2016-01-01' <= key <= '2016-09-31':
                has_2 = True

        if has_1 and has_2:
            new_codes.append(tmp['code'])

    return new_codes


async def handler_rst2(start1, end1, start2, end2, k=3, alpha=0.1, both_mins=False):
    '''
    获取两个时段k个最低价格的平均值，比较该平均值，符合条件的筛选出来
    k: 取k个最小成交量
    alpha： 取比区间一小，但是比区间一大aplpha
    both_mins 必须最小值同时存在于两个期间
    '''

    codes = await get_codes()

    if both_mins:
        new_codes = await get_both_min_codes(codes)

        print('new_codes', len(new_codes))
    else:
        new_codes = codes

    rsts1 = await fetch_volume(start1, end1, k=k, codes=new_codes)
    rsts2 = await fetch_volume(start2, end2, k=k, codes=new_codes)

    def _handler(rst):
        r = []
        for rec in rst:
            if len(rec['desc']) == 0:
                continue
            tmp = {}
            tmp['code'] = rec['desc'][0]['code']
            tmp['totals'] = rec['desc'][0]['totals']
            tmp['mean'] = rec['mink']['mean']

            r.append(tmp)
        return r

    r1 = _handler(rsts1)
    r2 = _handler(rsts2)

    df1 = pd.DataFrame.from_dict(r1)
    df2 = pd.DataFrame.from_dict(r2)

    df1.index = df1['code']
    del df1['code']
    df2.index = df2['code']
    del df2['code']
    del df2['totals']
    df2.columns = ['mean2']
    df = pd.concat([df1, df2, ], axis=1)
    df['alpha'] = (df['mean2'] - df['mean'])/df['mean2']
    # df['alpha'] = df['alpha'].apply(abs)
    df = df[df['alpha'] <= alpha]
    df = df.sort_values('totals')
    return df


async def process(file_name, start1, end1, start2, end2, k=3, alpha=0.1):
    df = await handler_rst2(start1, end1, start2, end2, k, alpha)
    print(df)
    print(set(df.index))
    df.to_excel(file_name)


@click.command()
@click.option('--file_name', default='volume.xlsx', help='file_name')
@click.option('--start1', default='2016-01-01', help='file_name')
@click.option('--end1', default='2016-09-30', help='file_name')
@click.option('--start2', default='2018-02-09', help='file_name')
@click.option('--end2', default='end', help='file_name')
@click.option('--k', default=3, help='file_name')
@click.option('--alpha', default=0.1, help='file_name')
def main(file_name, start1, end1, start2, end2, k, alpha):
    import time
    b = time.time()
    loop = asyncio.get_event_loop()
    if not file_name.endswith('.xlsx'):
        file_name = file_name + '.xlsx'
    loop.run_until_complete(
        process(file_name, start1, end1, start2, end2, k, alpha))
    e = time.time()
    print(e-b)


if __name__ == '__main__':
    main()
