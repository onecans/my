from .code_base import BaseInfoDb, CodeDb
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


def se_info(columns):
    raise NotImplementedError


def code_list(where='ALL'):
    db = BaseInfoDb()
    return db.stock_list(where=where)


__all__ = ['base_info', 'code_info', 'se_info', 'code_list']
