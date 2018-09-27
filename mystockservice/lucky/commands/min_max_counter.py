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


async def process(resample='1w', window_size=7*52,  min_timetomarket=None, test=False, where='ALL'):
    rsts = await util.fetch(URL,  resample=resample, window_size=window_size,
                            min_timetomarket=min_timetomarket, test=test, where=where)
    c = defaultdict(Counter)
    for rst in rsts:
        for key, value in rst['result'].items():
            c[key].update(**value)
    df = None
    for key, value in c.items():
        tmp = pd.DataFrame.from_dict(value, 'index', columns=[key])
        if df is None:
            df = tmp
        else:
            df = pd.concat([df, tmp], axis=1, sort=True)

    df.index = pd.DatetimeIndex(df.index)

    df = df.sort_index()
    ds = pd.date_range(min(df.index), max(df.index), freq=resample)

    df = df.reindex(ds,
                    copy=False, fill_value=0)
    # print(df)
    # x = df.plot()
    # plt.show()

    df = df.fillna(value=0)

    line1 = Line()

    line1.add('is_rolling_max', df.index, df['is_rolling_max'])

    line2 = Line()
    line2.add('is_rolling_min', df.index, df['is_rolling_min'])

    overlap = Overlap(
    )
    overlap.add(line1)
    overlap.add(line2)  # , yaxis_index=1, is_add_yaxis=True
    util.render(overlap, path="render.html",)

    line1 = Line()

    line1.add('ismax', df.index, df['ismax'])

    line2 = Line()
    line2.add('ismin', df.index, df['ismin'])

    overlap = Overlap(
    )
    overlap.add(line1)
    overlap.add(line2)
    util.render(overlap, path="render2.html",)
    # overlap.render(path="render2.html",)

    for c in df.columns:
        df[c] = pd.to_numeric(df[c])
    df = df.resample('1m').sum()

    market_size = await util.get_marketsize(where=where)
    market_size = pd.DataFrame.from_dict(market_size)
    market_size.index = pd.DatetimeIndex(market_size.index)
    df['marketsize'] = market_size
    df['ismin'] = df['ismin'] / df['marketsize']
    df['ismax'] = df['ismax'] / df['marketsize']

    line1 = Line()

    line1.add('ismax', df.index, df['ismax'])

    line2 = Line()
    line2.add('ismin', df.index, df['ismin'])

    overlap = Overlap(
    )
    overlap.add(line1)
    overlap.add(line2)
    util.render(overlap, path="render3.html",)
    return df


@click.command()
@click.option('--resample', default='1d', help='用于减少结果集，类似于周线，月线')
@click.option('--window_size', default=7*52, help='窗口')
@click.option('--min_timetomarket', default=20180101, help='用于去除近期上市的股票')
@click.option('--where', default='ALL', help='市场')
@click.option('--test', default=False, help='是否启用test, 只处理少量code')
def main(resample, window_size, min_timetomarket, where, test):
    """
    破新高和新低的股票数
    """
    print('='*50)
    print(f'破新高和新低的股票数')

    import time
    b = time.time()
    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        process(resample, window_size, min_timetomarket, test=True, where=where)
    )

    e = time.time()
    print(e-b)


if __name__ == '__main__':
    main()
