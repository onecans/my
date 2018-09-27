# encoding=utf-8
import os
from collections import OrderedDict
from multiprocessing.pool import Pool as ThreadPool

import pandas as pd
import tushare as ts
import time
from .basic import get_timeToMarket, get_code_list, LAST_MARKET_DAY, is_trade, get_outstanding, get_sh_code_list
from .settings import CACHE_DIR, ONLY_CACHE
from .utils import parse_code

DATE_FORMATE = '%Y-%m-%d'

import datetime
def _save_qfq(code, index=False):
    try:
        cache_file = cache_file_name(code, index)
        print(cache_file)
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, encoding='utf-8')
            df = df.set_index('date')
            max_date, min_date = df.index[0], df.index[-1]
            timeToMarket = get_timeToMarket(code)
            start_date = timeToMarket.strftime(DATE_FORMATE)
            last_market_day = datetime.datetime.strptime( LAST_MARKET_DAY,DATE_FORMATE)
            fetch_day = last_market_day - datetime.timedelta(days=7)

            if start_date == min_date and max_date >=  fetch_day.strftime(DATE_FORMATE):
                print(code, 'True, Cached')
                return True, cache_file, True

            if start_date == min_date and is_trade(code) is False:
                print(code, 'True, Cached and Not trade')
                return True, cache_file, True

        df = _get_qfq(code, index=index)

        df.to_csv(cache_file, encoding='utf-8')
        print(code, 'True, Cached Again')
        return True, cache_file, False
    except Exception as e:
        print('Error, ' + str(e.args))
        return False, cache_file, False


def cache_file_name(code, index=False):
    if index:
        cache_file = os.path.join(CACHE_DIR, 'his_qfq_index_%s.csv' % code)
    else:
        cache_file = os.path.join(CACHE_DIR, 'his_qfq_%s.csv' % code)
    return cache_file


# 获取前复权单价
def cache_qfq_his():
    """

    :param code:
    :param date: YYYY-MM-DD
    :return:
    """
    # pool = ThreadPool(5)
    # # for c in get_code_list():
    # for c in get_sh_code_list():
    #     _code = parse_code(c)

    #     pool.apply_async(_save_qfq, args=(_code,))

    # for c in ('000001'):

    #     pool.apply_async(_save_qfq, args=(c,True))

    # pool.close()
    # pool.join()
    import random
    for c in get_sh_code_list():
        _code = parse_code(c)

        status, cache_file, cached = _save_qfq(_code)
        if not cached:
            time.sleep(random.randint(60,60))

    for c in (['000001']):
        _save_qfq(c, True)
        time.sleep(random.randint(60,60))


def _get_qfq_from_163(code, bdate=None, edate=None, index=False):
    if bdate is None:
        timeToMarket = get_timeToMarket(code)
        start_date = timeToMarket.strftime('%Y%m%d')
    else:
        start_date = bdate.replace('-', '')

    if edate is None:
        end_date = LAST_MARKET_DAY.replace('-', '')
    else:
        end_date = edate.replace('-', '')
    _code = '0' + code
    fields = '%3b'.join(['TCLOSE', 'HIGH', 'LOW', 'TOPEN', 'LCLOSE', 'CHG', 'PCHG',
                        'TURNOVER', 'VOTURNOVER', 'VATURNOVER', 'TCAP', 'MCAP'])
    url = f'http://quotes.money.163.com/service/chddata.html?code={_code}&start={start_date}&end={end_date}&fields={fields}'
    df = pd.read_csv(url, encoding='gbk')
    df.columns = ['date','code','name','close','high','low','open','pre','change','chg','turnover','volume','amount','cap','famc']

    return df
# 获取前复权单价
# @retry(tries=10, delay=5)
# http://q.stock.sohu.com/hisHq?code=zs_000001&start=20000504&end=20151215&stat=1&order=D&period=d&callback=historySearchHandler&r=0.8391495715053367&0.9677250558488026

def _get_qfq(code, bdate=None, edate=None, index=False):
    """

    :param code:
    :param bdate 开始日期 yyyy-mm-dd:
    :param date 结束日期 yyyy-mm-dd:
    :param cache:
    :return:
    """

    if bdate is None:
        timeToMarket = get_timeToMarket(code)

        start_date = timeToMarket.strftime(DATE_FORMATE)
    else:
        start_date = bdate
    df = ts.get_h_data(code, start=start_date, autype='qfq', index=index)
    if df is None:
        return None
    if edate:
        return df[df.index <= edate]
    else:
        return df
def get_qfq(code, bdate=None, edate=None, index=False, cache=True):
    # print bdate,edate
    if ONLY_CACHE and cache:
        cache_file = cache_file_name(code, index)
        if not os.path.exists(cache_file):
            return None
    else:
        rst, cache_file, _ = _save_qfq(code, index)
        if rst is False:
            raise Exception('Error to get qfq')
    df = pd.read_csv(cache_file, encoding='utf-8')
    df.set_index('date', inplace=True)

    if edate:
        df = df[df.index <= edate]
    # print df
    if bdate:
        df = df[df.index >= bdate]
    return df


def get_price_times(code, bdate=None, edate=None,
                    begin_price_type='low', end_price_type='high'):
    """

    :param code: 代码
    :param bdate: 开始日期 '1997-05-12'
    :param edate: 结束日期 '1997-08-12'
    :param begin_price_type: 开始价格的类型 , close, open, high, low
    :param end_price_type: 结束价格的类型, close, open, high, low
    :return: OrderDict
    """

    _code = str(code).rjust(6, '0')

    df = get_qfq(code=_code, bdate=bdate, edate=edate)

    if df is None or df.empty:
        return None

    min_idx = df.idxmin(axis=0)[begin_price_type]
    min = df.loc[min_idx][begin_price_type]

    max_idx = df.idxmax(axis=0)[end_price_type]
    max = df.loc[max_idx][end_price_type]

    return float(max) / float(min)


def get_2d_price_times(code, bdate, edate=None,
                       begin_price_type='low', end_price_type='high'):
    """

    :param code: 代码
    :param bdate: 开始日期 '1997-05-12'
    :param edate: 结束日期 '1997-08-12'
    :param begin_price_type: 开始价格的类型 , close, open, high, low
    :param end_price_type: 结束价格的类型, close, open, high, low
    :return: float
    """

    _code = str(code).rjust(6, '0')

    df = get_qfq(code=_code, bdate=bdate, edate=edate)

    if df is None or df.empty:
        return None

    end = df.head(1)[end_price_type]
    begin = df.tail(1)[begin_price_type]

    return float(end) / float(begin)


def get_lowest(code, bdate=None, edate=None):
    """

    :param code: 代码
    :param bdate: 开始日期 '1997-05-12'
    :param edate: 结束日期 '1997-08-12'
    :return:
    """

    _code = str(code).rjust(6, '0')

    df = get_qfq(code=_code, bdate=bdate, edate=edate)

    if df is None or df.empty:
        return None

    min_idx = df.idxmin(axis=0)['low']
    min = df.loc[min_idx]['low']

    return {'date': min_idx, 'price': min}


def get_highest(code, bdate=None, edate=None):
    """

    :param code: 代码
    :param bdate: 开始日期 '1997-05-12'
    :param edate: 结束日期 '1997-08-12'
    :return:
    """

    _code = str(code).rjust(6, '0')

    df = get_qfq(code=_code, bdate=bdate, edate=edate)

    if df is None or df.empty:
        return None

    max_idx = df.idxmax(axis=0)['high']
    max = df.loc[max_idx]['high']

    return {'date': max_idx, 'price': max}


def get_fuqu_price(code, date):
    df = get_qfq(code, date, date)
    if df is None or df.empty:
        return 0
    return float(df['low'])


def get_price_update(code, bdate=None, edate=None):
    _code = str(code).rjust(6, '0')
    df = get_qfq(code=_code, bdate=bdate, edate=edate)
    if df is None or df.empty:
        return 0

    high_idx = df.idxmax(axis=0)['high']
    high = df.loc[high_idx]['high']
    low_idx = df.idxmin(axis=0)['low']
    low = df.loc[low_idx]['low']
    if high_idx > low_idx:
        update = (high - low) / low
    else:
        update = (low - high) / high

    return update


def get_price_avg(code, bdate, edate, days=5):
    _code = str(code).rjust(6, '0')
    df = get_qfq(code=_code, bdate=bdate, edate=edate)
    if df is None or df.empty:
        return 0

    begin_df = df.tail(days)
    end_df = df.head(days)

    # print begin_df,
    # print end_df
    begin_idx = begin_df.idxmin(axis=0)['low']
    begin = begin_df.loc[begin_idx]['low']
    end_idx = end_df.idxmax(axis=0)['high']
    end = end_df.loc[end_idx]['high']

    # print end, begin
    # print begin_idx,end_idx
    update = (end - begin) / begin

    return update


def get_price_update_list(code, bdate, edate, days=1):
    _code = str(code).rjust(6, '0')
    df = get_qfq(code=_code, bdate=bdate, edate=edate)
    if df is None or df.empty or len(df) <= days + 1:
        return None
    # if df is None or df.empty:
    #      return None

    begin_df = df.tail(days)
    begin_idx = begin_df.idxmin(axis=0)['low']
    begin = begin_df.loc[begin_idx]['low']

    outstanding = get_outstanding(code)

    if not outstanding:
        return None

    # 最少取1天之后的数据进行计算
    # _bdate = df.index[-1 * (days + 5)]
    _bdate = df.index[-1 * (days + 1)]
    update_dict = OrderedDict()

    for d in pd.date_range(_bdate, edate):
        _data = dict()
        _date = d.strftime('%Y-%m-%d')
        try:
            end = df.loc[_date]['high']
        except KeyError:
            continue
        update = (end - begin) / begin
        _data['update'] = update

        if update <= -0.35:
            _data['per10_2'] = -40
        elif update >= 0.35:
            _data['per10_2'] = 40
        else:
            _data['per10_2'] = round(update / 0.1) * 10

        # _data['per3'] = round(update / 0.03) * 3
        _data['per10'] = round(update / 0.1) * 10

        _data['cnt'] = ((outstanding) * end) / 1000000000

        print(_data['per10'], _data['cnt'])
        # _data['per15'] = round(update / 0.15) * 15
        # _data['per20'] = round(update / 0.2) * 20
        # _data['per25'] = round(update / 0.25) * 25
        # _data['per30'] = round(update / 0.3) * 30
        # _data['per40'] = round(update / 0.4) * 40
        # _data['per50'] = round(update / 0.5) * 50

        # _data['per50'] = round(update/100 ) * 100
        update_dict[_date] = _data
        # print update_dict
    return update_dict


if __name__ == '__main__':
    cache_qfq_his()
