from itertools import chain

import pandas as pd
import tushare as ts

from mystockdata import _pytdx, db


class CodeIndexDb(db.DfDb):
    prefix = 'code_index'

    def __init__(self, code, **kwargs):
        super().__init__(**kwargs)
        self.db = self.db.prefixed_db(db.force_bytes(self.prefix+code))


class CodeDb(db.DatetimeIndexMixin, db.DfDb):
    prefix = 'code_'

    def __init__(self, code, **kwargs):
        super().__init__(**kwargs)
        self.db = self.db.prefixed_db(db.force_bytes(self.prefix+code))


# class CodeDb():
#     array_db_columns = ['open', 'high',
#                         'low', 'close', 'volume', 'amount',
#                         'bfq_open', 'bfq_high',
#                         'bfq_low', 'bfq_close', 'bfq_volume', 'bfq_amount', ]

#     def __init__(self, code, **kwargs):
#         self.index_db = CodeIndexDb(code=code, **kwargs)
#         self.array_db = CodeArrayDb(code=code, **kwargs)

#     def columns_group(self, columns):

#         d = defualtdict(dict)
#         for c in columns:
#             if c in self.array_db_columns:
#                 d['array_db'].append(c)
#             else:
#                 d['index_db'].append(c)

#     def read(self, columns):
#         cg = self.columns_group(columns)
#         if 'array_db' in cg:
#             df = self.array_db.read(cg['array_db'])
#         else:
#             raise ValueError('必须查询ArrayDB 列')

#         if 'index_db' in cg:
#             tmp = self.index_db.read(cg['index_db'])

#             df = df.fillna(method='ffill')
#             df = df.fillna(method='bfill')
#             return df

#     def save(self, df):
#         cg = self.columns_group(columns)

#     def delete(self, columns):
#         cg = self.columns_group(columns)

#     def keys(self):
#         return chain(self.index_db.keys(), self.array_db.keys())

#     def values(self):
#         return chain(self.index_db.values(), self.array_db.values())

#     def items(self):
#         return chain(self.index_db.items(), self.array_db.items())


class BaseInfoDb(db.PrefixedDfDb):
    prefix = 'baseinfo'

    def stock_list(self, where="ALL"):
        df = self.read(['sse'])
        if where == 'ALL':
            tmp = df.index
        elif where == 'SH':
            tmp = df[df['sse'] == 'sh'].index
        elif where == 'SZ':
            tmp = df[df['sse'] == 'sz'].index
        else:
            raise ValueError('where can only be ALL, SH, SZ')
        return tmp.tolist()


def stock_list(where='ALL'):
    return BaseInfoDb().stock_list(where=where)


def sync():
    base_info = ts.get_stock_basics()

    _pytdx.get_ip()
    stock_list = _pytdx.QA_fetch_get_stock_list()
    stock_list.index = stock_list.code
    del stock_list['name']
    df = pd.concat([base_info, stock_list], axis=1, sort=True)
    BaseInfoDb().save(df)


def main():
    print(BaseInfoDb().stock_list('SZ'))


if __name__ == '__main__':
    main()
