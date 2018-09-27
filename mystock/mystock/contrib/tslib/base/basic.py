# encoding=utf-8
import datetime
import os

import pandas as pd
import tushare as ts

from .settings import CACHE_DIR
from .utils import parse_code
today = datetime.datetime.today().strftime('%Y%m%d')
CACHE_FILE = os.path.join(CACHE_DIR, 'stock_basics.' + today)

if not os.path.exists(CACHE_FILE):
    stock_basics = ts.get_stock_basics()
    stock_basics.to_csv(CACHE_FILE, encoding='utf-8')

stock_basics = pd.read_csv(CACHE_FILE)
stock_basics = stock_basics.set_index('code')

sh_realtime_quotes = ts.get_realtime_quotes('sh')
LAST_MARKET_DAY=str(sh_realtime_quotes['date'][0]) # %Y-%m-%d
TODAY_CACHE_FILE = os.path.join(CACHE_DIR, 'today_all.' + today)

if not os.path.exists(TODAY_CACHE_FILE):
    today_all = ts.get_today_all()
    today_all.to_csv(TODAY_CACHE_FILE, encoding='utf-8')


today_all = pd.read_csv(TODAY_CACHE_FILE)
today_all = today_all.set_index(u'code')


def is_trade(code):
    _code = int(code)
    return not ( today_all.loc[_code]['open'] == 0 and today_all.loc[_code]['high'] == 0 and today_all.loc[_code]['low'] == 0)



# 获取流通股
def get_outstanding(code):
    _code = int(code)
    return float(stock_basics.loc[_code]['outstanding']) * 10000

# 获取交易额
def get_amount(code):
    _code = int(code)
    return float(stock_basics.loc[_code]['amount'])


def get_outstanding_sum():
    return float(stock_basics.sum['outstanding']) * 10000

# 获取流通股比例
def get_outstanding_per(code):
    _code = int(code)
    return float(stock_basics.loc[_code]['outstanding']) / float(stock_basics.sum()['outstanding'])


# 获取总股本
def get_totals(code):
    _code = int(code)
    try:
        return float(stock_basics.loc[_code]['totals']) * 10000
    except:
        return 999

# 获取总股本 亿
def get_totals_amount(code):
    _code = int(code)
    try:
        return float(stock_basics.loc[_code]['totals']) * float(get_today_settlement(code)) 
    except:
        return 999

# 获取名字
def get_name(code):
    _code = int(code)
    try:
        return str(stock_basics.loc[_code]['name'])
    except:
        return '没找到'


# 获取上市时间
def get_timeToMarket(code):
    _code = int(code)
    try:
        return datetime.datetime.strptime(str(stock_basics.loc[_code]['timeToMarket']), '%Y%m%d').date()
    except:
        return None


def get_code_list():
    return list(stock_basics.index)



def get_sh_code_list():
    return [i for i in list(stock_basics.index) if parse_code(i).startswith('6')]


# 获取当天未复权价格
def get_today_trade(code):
    _code = int(code)
    try:
        return float(today_all.loc[_code]['trade'])
    except:
        return 999


# 获取当天收盘价
def get_today_settlement(code):
    _code = int(code)
    try:
        return float(today_all.loc[_code]['settlement'])
    except:
        return 999
