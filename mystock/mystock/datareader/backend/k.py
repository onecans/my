import os
import pathlib
import pandas as pd
from .base import CodeIndexDfMixin, DfMixin

CSV_DIR = '/data/stock/tdx/qfq'


class KFilePath(pathlib.Path):
    columns = ['date', 'open', 'high',
               'low', 'close', 'volume', 'amount']

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def df(self):
        tmp = pd.read_csv(self, skiprows=1, engine='python',
                          encoding='gbk', sep='\t', nrows=nrows)
        tmp.columns = self.columns
        tmp.index = pd.DatetimeIndex(df['date'])
        del tmp['date']
        return tmp


class Code(CodeIndexDfMixin):
    file_path = '/data/stock/k'

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'code'

    def down_load(self):
        path = pathlib.Path(CSV_DIR)
        l = list()
        for root, dirs, files in os.walk(path):
            for f in files:
                tmp = {}
                p = path.joinpath(f)
                if p.name.startswith('SH#'):
                    tmp = {'type': 'SH', 'file_name': str(p), 'code': p.name.split('#')[1].split('.')[0]}
                elif p.name.startswith('SZ#'):
                    tmp = {'type': 'SZ', 'file_name': str(p), 'code': p.name.split('#')[1].split('.')[0]}
                else:
                    try:
                        _ = int(p.name[0])
                        tmp = {'type': 'IDX', 'file_name': str(p), 'code': 'index_' + p.name.split('.')[0]}
                    except:
                        continue

                l.append(tmp)

        return pd.DataFrame(data=l, index=[x['code'] for x in l])


class _ColumnStore(DfMixin):
    file_path = '/data/stock/k'
    code = Code()

    @property
    def col_name(self):
        raise NotImplemented()

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / self.col_name

    def can_down_load(self, dates):
        df = KFilePath(self.code.loc['000001'].filename).df()
        if max(df.index) > min(dates):
            return True
        else:
            return False

    def down_load(self, dates):
        if not self.can_down_load(dates):
            return None

        for c, row in self.code.iterrows():
            pass
