from .code_base import BaseInfoDb, CodeDb
from .market import MarketDb
from .se import SE


def base_info(columns, codes=None):
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
