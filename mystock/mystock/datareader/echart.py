import concurrent.futures
import math

import numpy as np
import pandas as pd
from datareader import backend
from datareader.base import RZRQ, SE
from pyecharts import *
from pyecharts import Overlap

from . import services


def float_reindex(df1, df2):

    def float_range(start, end, stop):
        s = start - stop
        e = end
        while round(s, 1) < round(e-stop, 1):
            s = s+stop
            yield round(s, 1)

    start = min(min(df1.index), min(df2.index))
    end = max(max(df1.index), max(df2.index))

    df1 = df1.reindex(pd.Float64Index(float_range(start, end, 0.1)))
    df2 = df2.reindex(pd.Float64Index(float_range(start, end, 0.1)))

    return df1, df2


def get_range_bar(start, end, where='', sample='', fq_type='qfq'):
    '''
    bar1,df1 = get_range_bar('get_max_range2', '2015-05-15','2018-01-31',  where='SH',fq_type='qfq')
    bar2,df2 = get_range_bar('get_current_range2', '2015-05-15','2018-01-31',  where='SH',fq_type='qfq')
    '''

    _start_show = start if start else '1990'
    _end_show = end if end else 'current'

    backend.FQ_TYPE = fq_type
    df = backend.all('get_max_range2', start, end, sample=sample, where=where)
    df2 = round(df, 1)
    df3 = df2.groupby('val').size()

    df = backend.all('get_current_range2', start, end, sample=sample, where=where)
    df2 = round(df, 1)
    df4 = df2.groupby('val').size()

    df3, df4 = float_reindex(df3, df4)

    line = Bar()
    line.add('{_start_show}-{_end_show}-跌幅-{fq_type}-{where}-数量_max'.format(**locals()), df3.index, df3)

    line2 = Bar()
    line2.add('数量_current', df4.index, df4)

    overlap = Overlap()
    overlap.add(line)
    # 新增一个 y 轴，此时 y 轴的数量为 2，第二个 y 轴的索引为 1（索引从 0 开始），所以设置 yaxis_index = 1
    # 由于使用的是同一个 x 轴，所以 x 轴部分不用做出改变
    overlap.add(line2, yaxis_index=1, is_add_yaxis=True)

    return overlap, df3, df4


def get_grow_range_bar(start, end, where='', sample='', fq_type='qfq'):
    '''
    bar1,df1 = get_range_bar('get_max_range2', '2015-05-15','2018-01-31',  where='SH',fq_type='qfq')
    bar2,df2 = get_range_bar('get_current_range2', '2015-05-15','2018-01-31',  where='SH',fq_type='qfq')
    '''
    # sample = 10
    _start_show = start if start else '1990'
    _end_show = end if end else 'current'

    backend.FQ_TYPE = fq_type
    df = backend.all('get_max_grow_range2', start, end, sample=sample, where=where)
    df2 = round(df, 1)
    df3 = df2.groupby('val').size()

    df = backend.all('get_current_grow_range2', start, end, sample=sample, where=where)
    df2 = round(df, 1)
    df4 = df2.groupby('val').size()

    df3, df4 = float_reindex(df3, df4)

    line = Bar()
    line.add('{_start_show}-{_end_show}-涨幅-{fq_type}-{where}-数量_max'.format(**locals()), df3.index, df3)

    line2 = Bar()
    line2.add('数量_current', df4.index, df4)

    overlap = Overlap()
    overlap.add(line)
    # 新增一个 y 轴，此时 y 轴的数量为 2，第二个 y 轴的索引为 1（索引从 0 开始），所以设置 yaxis_index = 1
    # 由于使用的是同一个 x 轴，所以 x 轴部分不用做出改变
    overlap.add(line2, yaxis_index=1, is_add_yaxis=True)

    return overlap, df3, df4


def get_max_date_bar(start, end,  where='', sample='', fq_type='qfq', **kwargs):
    '''
    'high.idxmax'
    df3, bar3_cnt, bar3_val = get_max_date_bar(start='2015-06-12', end='2017-11-22',val_name='high.idxmax',where='SH')
    df4, bar4_cnt, bar4_val = get_max_date_bar(start='2015-06-12', end='2018-1-26',val_name='high.idxmax',where='SH')

    '''
    _start_show = start if start else '1990'
    _end_show = end if end else 'current'
    val_name = kwargs['val_name']
    backend.FQ_TYPE = fq_type
    df = backend.all('get_df_val', start, end, sample=sample, where=where, val_name=val_name,)
    try:
        df = df.drop(df[df['val'] == 0].index)
    except:
        pass

    df2 = df.groupby('val').size().sort_index()
    df2.index = pd.DatetimeIndex(df2.index)

    market_val = backend.get_market_val()
    df['market_val'] = market_val
    df3 = df.groupby('val').sum()

    print(type(df2))

    df2, df3 = reindex([df2, df3], method=None, fill_value=0)
    print(df2, df3)

    df2 = df2.resample('W').sum()
    df3 = df3.resample('W').sum()

    line = Line()
    line.add('数量 | {_start_show} 至 {_end_show} | {where}-{fq_type}'.format(**locals()), df2.index, df2)

    line2 = Line()
    line2.add('市值', df3.index, df3.market_val)

    overlap = Overlap()
    overlap.add(line)
    # 新增一个 y 轴，此时 y 轴的数量为 2，第二个 y 轴的索引为 1（索引从 0 开始），所以设置 yaxis_index = 1
    # 由于使用的是同一个 x 轴，所以 x 轴部分不用做出改变
    overlap.add(line2, yaxis_index=1, is_add_yaxis=True)

    return overlap, df2, df3


def get_line(code, start=None, end=None, index=False, cache=True, field='high', alpha=0, test=False):

    def _handler_df(df):
        n = alpha / 365
        l = len(df)

        def _p3(args):
            l_ns = l - len(args)
    #         print(math.pow( 1+n, l_ns ))
            return args[-1] * math.pow(1 + n, l_ns)

        return df.expanding(1).apply(_p3)
    if test:
        dates = pd.date_range('1991-01-01', '2017-12-31')
        df = pd.DataFrame({'high': [1, ] * len(dates)}, index=dates)

    else:
        df = backend.get_df(code, start=start, end=end, index=index)

    df = _handler_df(df)

    line = Line()
    if index:
        show = 'index：{code}'.format(**locals())
    else:
        show = code
    if alpha:
        show = '{show}-alpha：{alpha}'.format(**locals())

    df = df.reindex(pd.date_range(min(df.index), max(df.index)), method='bfill')
    line.add(show, df.index, df.high, is_more_utils=True)
    return line, df


def reindex(dfs, method='bfill', fill_value=np.NaN):
    tmp = []
    for df in dfs:
        tmp.append(df.dropna(how='all'))

    start = min([min(df.index) for df in tmp])
    end = max([max(df.index) for df in tmp])
    _tmp = []
    for df in tmp:
        df = df.reindex(pd.date_range(start, end), method=method, copy=False, fill_value=fill_value)
        _tmp.append(df)
    return _tmp


indexs = {'SHA': '999999', 'SH': '999999', 'SZ': '399001',
          'ZXQY': '399005', 'CYB': '399006', 'SZZB': '399001', 'SHB': '999999'}


def _check_category(category):
    if category not in ('SHA', 'SHB', 'SH', 'SZ', 'CYB', 'ZXQY', 'SZZB'):
        print('ERROR, VALID category: ', 'SHA', 'SHB', 'SH', 'SZ', 'CYB', 'ZXQY', 'SZZB')
        return False

    return True


def show_overview_day2(category, method, name):
    # if not _check_category(category):
    #     return

    se = SE()
    m = getattr(se, method)
    _df1 = m()
    df1 = _df1[[category, ]]
    _, df2 = get_line(indexs.get(category, '000001'), index=True)
    df1, df2 = reindex([df1, df2])

    line1 = Line()
    if method in ('get_market_val', 'get_negotiable_val') \
            and category in ('SZ', 'CYB', 'ZXQY'):
        line1.add(name, df1.index, df1[category] / 100000000, is_datazoom_show=False)
    else:
        line1.add(name, df1.index, df1[category], is_datazoom_show=False)
    line2 = Line()
    line2.add('index: %s' % indexs.get(category, '000001'), df2.index, df2.high, is_datazoom_show=True)

    overlap = Overlap()
    overlap.add(line1)
    # 新增一个 y 轴，此时 y 轴的数量为 2，第二个 y 轴的索引为 1（索引从 0 开始），所以设置 yaxis_index = 1
    # 由于使用的是同一个 x 轴，所以 x 轴部分不用做出改变
    overlap.add(line2, yaxis_index=1, is_add_yaxis=True)
    return overlap


def reindex2(dfs, method='bfill', fill_value=np.NaN):

    start = min([min(df.index) for df in dfs])
    end = max([max(df.index) for df in dfs])
    print(start, end)
    _tmp = []
    for df in dfs:
        df = df.reindex(pd.date_range(start, end), method=method, copy=False)
        _tmp.append(df)
    return _tmp


def show_overview_day(category, method, name):

    # if not _check_category(category):

    index_data = services.line(indexs.get(category, '999999'), 'start', 'end', col='high')
    se_data = services.se(method[4:], category)

    df1 = pd.DataFrame.from_dict(index_data)
    df1.index = pd.DatetimeIndex(df1.index)

    df2 = pd.DataFrame.from_dict(se_data)
    df2.index = pd.DatetimeIndex(df2.index)

    df1, df2 = reindex2([df1, df2])
    print(df1)
    print(df2)
    line1 = Line()
    line1.add(name, df2.index, df2[category.upper()], is_datazoom_show=False)
    line2 = Line()
    line2.add('index: %s' % indexs.get(category, '999999'),
              df1.index, df1['high'], is_datazoom_show=True)

    overlap = Overlap()
    overlap.add(line1)
    # 新增一个 y 轴，此时 y 轴的数量为 2，第二个 y 轴的索引为 1（索引从 0 开始），所以设置 yaxis_index = 1
    # 由于使用的是同一个 x 轴，所以 x 轴部分不用做出改变

    overlap.add(line2, yaxis_index=1, is_add_yaxis=True)
    return overlap


def negotiable_val(category):
    if _check_category(category):
        return show_overview_day(category, 'get_negotiable_val', '流通市值')
    elif category == 'ALL':
        page = Page()
        for c in ('SHA', 'SZ', 'CYB', 'ZXQY'):
            page.add(show_overview_day(c, 'get_negotiable_val', '流通市值-%s' % c))
        # page.render('staticfiles/show/negotiable_val.html')
        return page


def market_val(category):
    if _check_category(category):
        return show_overview_day(category, 'get_market_val', '市值')
    elif category == 'ALL':
        page = Page()
        for c in ('SHA', 'SZ', 'CYB', 'ZXQY'):
            page.add(show_overview_day(c, 'get_market_val', '市值-%s' % c))
        # page.render('staticfiles/show/market_val.html')
        return page


def pe(category):
    if _check_category(category):
        return show_overview_day(category, 'get_pe', 'PE')
    elif category == 'ALL':
        page = Page()
        for c in ('SHA', 'SZ', 'CYB', 'ZXQY'):
            page.add(show_overview_day(c, 'get_pe', 'PE-%s' % c))
        # page.render('staticfiles/show/pe.html')
        return page


def _rzrq(code, start='2010-03-31', end=None, index=False):
    name = '融资余额(亿)'
    rzrq_field = 'rzye'
    rzrq = RZRQ()
    df1 = rzrq.get_rzrq(code=code, index=index)
    _, df2 = get_line(code, start=start, end=end, index=index)

    df1, df2 = reindex([df1, df2])

    line1 = Line()
    line1.add(name, df1.index, df1[rzrq_field] / 100000000)

    line2 = Line()
    line2.add('code: %s' % code, df2.index, df2.high)

    overlap = Overlap()
    overlap.add(line1)
    # 新增一个 y 轴，此时 y 轴的数量为 2，第二个 y 轴的索引为 1（索引从 0 开始），所以设置 yaxis_index = 1
    # 由于使用的是同一个 x 轴，所以 x 轴部分不用做出改变
    overlap.add(line2, yaxis_index=1, is_add_yaxis=True)
    return overlap


def rzrq(code, start='2010-03-31', end=None, index=False):
    if code != 'ALL':
        return _rzrq(code, start=start, end=end, index=index)
    else:
        page = Page()
        for code in ('000001', '399001'):
            l = _rzrq(str(code), index=True)
            page.add(l)

        for code in (601088, 601668, 601898, 601992, 601318, 601600, 601390):
            l = _rzrq(str(code), index=False)
            page.add(l)
        page.render('staticfiles/show/rzrq.html')
        return page
