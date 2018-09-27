import datetime
import json
import pathlib
import time

import pandas as pd
import requests

from .base import IndexDfMixin
from .k import Code


class SDGD(IndexDfMixin):
    file_path = '/data/stock/sdgd'
    code = Code().df()

    def __init__(self):
        pass

    def down_load(self):
        print('down_load')

        def _fetch(code, date):
            print('download code:', code)
            s = None

            url = 'http://data.eastmoney.com/DataCenter_V3/gdfx/stockholder.ashx?code=[CODE]&date=[DATE]&type=Lt'.replace(
                '[CODE]', code).replace('[DATE]', date)

            while True:
                if s is None:
                    s = requests.Session()
                try:
                    r = s.get(url).json()
                    df = pd.DataFrame.from_dict(r['data'])
                    df['code'] = int(code)
                    df['date'] = date

                    break
                except Exception as e:
                    print(e.args)
                    print('sleep...')
                    time.sleep(60)
                    s = requests.Session()

            return df
        if self.df_file.exists():
            df = pd.read_feather(self.df_file)
            codes = df['code'].unique()
        else:
            df = None
            codes = []

        date = '2018-03-31'

        i = 0
        for idx, c in enumerate(self.code.index):
            if int(c) in codes:
                print('pass ', c)
                continue
            i += 1
            tmp = _fetch(c, date)

            if df is None:
                df = tmp
            else:
                df = pd.concat([df, tmp])
            if i > 50:
                break

            time.sleep(1)

        df = df.reset_index(drop=True)
        df['idx'] = df.index
        df['BDBL'] = df['BDBL'].replace('-', 0)
        df['BDSUM'] = df['BDSUM'].replace('-', 0)
        return df

    @property
    def df_file(self):
        return pathlib.Path(self.file_path) / f'sdgd'

    def valid_codes(self):
        if self.df_file.exists():
            tmp = pd.read_feather(self.df_file)
            return tmp['code']
        else:
            return []

    def df(self):
        df = self._df()
        df['code'] = df['code'].apply(lambda x: str(x).rjust(6, '0'))
        return df
