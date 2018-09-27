'''
期间破新低股票数
'''
import asyncio
import math
import sys
from collections import Counter, defaultdict
from pprint import pprint

import aiohttp
import async_timeout
import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyecharts import Bar as Line
from pyecharts import Overlap

from lucky.commands import util

URL = '/k/min_max_counter/{code}?resample={resample}&window_size={window_size}'


async def process(start, end, resample='1w', window_size=7*52,  min_timetomarket=None, test=False, where='ALL', periods=None):
    rsts = await util.fetch(URL,  resample=resample, window_size=window_size,
                            min_timetomarket=min_timetomarket, test=test, where=where)
    c = defaultdict(Counter)
    cnt = Counter()
    codes = defaultdict(list)
    for rst in rsts:
        for key, value in rst['result'].items():
            if key != 'ismin':
                continue
            for period in periods:
                df = pd.DataFrame.from_dict(value, 'index', columns=[key])
                df.index = pd.DatetimeIndex(df.index)
                start = period[0]
                end = period[1]
                key = '%s === %s' % period
                df = df[df.index <= end]
                if not df.empty:
                    df = df[df.index >= start]
                if not df.empty:
                    cnt[key] += 1
                    codes[key].append(rst['paras']['code'])

    market_size = await util.get_marketsize(where=where)
    market_size = pd.DataFrame.from_dict(market_size)
    market_size.index = pd.DatetimeIndex(market_size.index)
    print('='*50)
    for period in periods:
        start = period[0]
        end = period[1]
        key = '%s === %s' % period

        print(where, start, ':', end, '|',
              '新低:', cnt[key], '股票数:', market_size.loc[end]['cnt'], '占比:', round(
                  cnt[key]/market_size.loc[end]['cnt'], 2))
        # print('破新低股票数： ', cnt[key])
        # print('当时', where, '股票数：', market_size.loc[end]['cnt'])
        # print('破新低股票数占比： ', cnt[key]/market_size.loc[end]['cnt'])
        # print('破新低股票列表: ', codes[key])

    print(codes)
    #         c[key].update(**value)
    # df = None
    # for key, value in c.items():
    #     tmp = pd.DataFrame.from_dict(value, 'index', columns=[key])
    #     if df is None:
    #         df = tmp
    #     else:
    #         df = pd.concat([df, tmp], axis=1, sort=True)

    # df.index = pd.DatetimeIndex(df.index)

    # df = df.sort_index()
    # ds = pd.date_range(min(df.index), max(df.index), freq=resample)

    # df = df.reindex(ds,
    #                 copy=False, fill_value=0)
    # # print(df)
    # # x = df.plot()
    # # plt.show()

    # df = df.fillna(value=0)

    # line1 = Line()

    # line1.add('is_rolling_max', df.index, df['is_rolling_max'])

    # line2 = Line()
    # line2.add('is_rolling_min', df.index, df['is_rolling_min'])

    # overlap = Overlap(
    # )
    # overlap.add(line1)
    # overlap.add(line2)  # , yaxis_index=1, is_add_yaxis=True
    # util.render(overlap, path="render.html",)

    # line1 = Line()

    # line1.add('ismax', df.index, df['ismax'])

    # line2 = Line()
    # line2.add('ismin', df.index, df['ismin'])

    # overlap = Overlap(
    # )
    # overlap.add(line1)
    # overlap.add(line2)
    # util.render(overlap, path="render2.html",)
    # # overlap.render(path="render2.html",)

    # for c in df.columns:
    #     df[c] = pd.to_numeric(df[c])
    # df = df.resample('1m').sum()

    # market_size = pd.DataFrame.from_dict(market_size)
    # market_size.index = pd.DatetimeIndex(market_size.index)
    # df['marketsize'] = market_size
    # df['ismin'] = df['ismin'] / df['marketsize']

    # line1 = Line()

    # line1.add('ismax', df.index, df['ismax'])

    # line2 = Line()
    # line2.add('ismin', df.index, df['ismin'])

    # overlap = Overlap(
    # )
    # overlap.add(line1)
    # overlap.add(line2)
    # util.render(overlap, path="render3.html",)
    # return df


@click.command()
@click.option('--start', default='2018-01-01', help='期间开始日期')
@click.option('--end', default='2018-02-01', help='期间结束日期')
@click.option('--resample', default='1d', help='用于减少结果集，类似于周线，月线')
@click.option('--window_size', default=52*7, help='窗口')
@click.option('--min_timetomarket', default=20370101, help='用于去除近期上市的股票')
@click.option('--where', default='ALL', help='市场')
@click.option('--test', default=False, help='是否启用test, 只处理少量code')
@click.option('--periods', help='一次输出多个期间')
def main(start, end, resample, window_size, min_timetomarket, where, test, periods):
    """
    期间内破新低的股票数，和占比
    """

    import time
    b = time.time()
    loop = asyncio.get_event_loop()
    _periods = [(x.split(':')[0], x.split(':')[-1])
                for x in periods.split(',')]

    print('期间列表：', _periods)
    loop.run_until_complete(
        process(start, end, resample, window_size,
                min_timetomarket, test=test, where=where, periods=_periods)
    )

    e = time.time()
    print(e-b)


if __name__ == '__main__':
    main()
