from .code_base import BaseInfoDb, CodeDb
from .market import MarketDb
from .se import SE


def base_info(columns, codes=None):
    '''
    code,代码
    name,名称
    industry,所属行业
    area,地区
    pe,市盈率
    outstanding,流通股本(亿)
    totals,总股本(亿)
    totalAssets,总资产(万)
    liquidAssets,流动资产
    fixedAssets,固定资产
    reserved,公积金
    reservedPerShare,每股公积金
    esp,每股收益
    bvps,每股净资
    pb,市净率
    timeToMarket,上市日期
    undp,未分利润
    perundp, 每股未分配
    rev,收入同比(%)
    profit,利润同比(%)
    gpr,毛利率(%)
    npr,净利润率(%)
    holders,股东人数
    '''
    db = BaseInfoDb()
    df = db.read(columns=columns)
    print(columns, codes)
    if codes:
        df = df[df.index.isin(codes)]

    return df


def code_info(code, columns):
    db = CodeDb(code)
    return db.read(columns=columns)


def se_info(column, category=None):
    if column not in ('pe', 'market_val', 'negotiable_val', 'avg_price'):
        raise NotImplementedError

    method = 'get_%s' % column
    obj = SE()
    df = getattr(obj, method)()
    if category == 'sh':
        return df['SHA', 'SHB', 'SH']
    return df[[category.upper()]]


def code_list(where='ALL'):
    db = BaseInfoDb()
    return db.stock_list(where=where)


def market_info(columns, where='ALL'):
    db = MarketDb(where)
    return db.read(columns=columns)


__all__ = ['base_info', 'code_info', 'se_info', 'code_list', 'market_info']
