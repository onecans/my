import glob
import pathlib
from collections import UserDict

import numpy as np
import pandas as pd

from .base import CodeIndexDfMixin

CSV_DIR = '/data/stock/tdx/qfq'


class Info(UserDict, CodeIndexDfMixin):
    file_path = '/data/stock/info'

    def __init__(self):
        self.data = self.df()

    def __iter__(self):
        return self.data.iterrows()

    # Modify __contains__ to work correctly when __missing__ is present
    def __contains__(self, key):
        return key in self.data.index

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'info'

    def down_load(self):
        print('down_load')
        path = pathlib.Path(CSV_DIR) / '沪深Ａ股*.txt'
        _path = sorted(glob.glob(str(path)))[-1]

        df = pd.read_csv(_path, sep='\t', encoding='gbk', skipfooter=1, engine='python', dtype={'代码': np.str})
        df = df.assign(code=lambda df: df['代码'])
        df.set_index('code', inplace=True, drop=True)
        del df['代码']
        return df

    def __getitem__(self, key):
        try:
            return self.df().loc[key]
        except KeyError:
            return self.df().loc[str(key)]


class IndexInfo(Info):
    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / 'index_info'

    def __getitem__(self, key):
        _key = 'index_{key}'.format(**locals())
        try:
            return self.df().loc[_key]
        except KeyError:
            return self.df().loc[str(_key)]
