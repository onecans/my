import pandas as pd
import tushare as ts

from mystockdata import _pytdx, db


class CodeDb(db.DatetimeIndexMixin, db.DfDb):
    prefix = 'code_'

    def __init__(self, code, **kwargs):
        super().__init__(**kwargs)
        self.db = self.db.prefixed_db(db.force_bytes(self.prefix+code))


class BaseInfoDb(db.PrefixedDfDb):
    prefix = 'baseinfo'

    def stock_list(self, where="ALL"):
        df = self.read(['sse'])
        if where == 'ALL':
            tmp = df.index
        elif where == 'SH':
            tmp = df[df['sse'] == 'sh'].index
        elif where == 'SZ':
            tmp = df[df['sse'] == 'sh'].index
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
    df = pd.concat([base_info, stock_list], axis=1, sort=True)
    BaseInfoDb().save(df)


def main():
    print(BaseInfoDb().stock_list('SZ'))


if __name__ == '__main__':
    main()
