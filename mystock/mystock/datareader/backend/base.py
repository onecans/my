import datetime
import time
import numpy as np
import pandas as pd
import pathlib
import shutil
import os


def handler(df):
    def func(c):
        try:
            return pd.to_numeric(df[c])
        except:
            return 
    t = {}
    for c in df.columns:
        t[c] = func(c)

    df = df.dropna(how='all')
    df = df.assign(**t)
    return df


class DfCacheMixin:
    cache_time = 60 * 60

    @property
    def cache_df(self):
        if hasattr(self, '_dfmixin_df_time') and hasattr(self, '_dfmixin_df'):
            if time.time() - self._dfmixin_df_time > self.cache_time:
                delattr(self, '_dfmixin_df')
                delattr(self, '_dfmixin_df_time')

            if hasattr(self, '_dfmixin_df'):
                return self._dfmixin_df
            else:
                return None


class DfMixin(DfCacheMixin):
    @property
    def df_file(self):
        raise NotImplementedError

    def down_load(self, dates, *args, **kwargs):
        raise NotImplementedError

    def to_feathre(self, df_file):
        if not isinstance(df_file, pathlib.Path):
            _tmp = pathlib.Path(df_file + '.tmp')
        else:
            _tmp = pathlib.Path(str(df_file) + '.tmp')

        self._dfmixin_df['date'] = self._dfmixin_df.index.strftime('%Y-%m-%d')
        self._dfmixin_df = handler(self._dfmixin_df)
        self._dfmixin_df.reset_index(inplace=True, drop=True)
        self._dfmixin_df.to_feather(_tmp)
        _tmp.rename(df_file)
        self._dfmixin_df.index = pd.DatetimeIndex(self._dfmixin_df['date'])
        del self._dfmixin_df['date']

    def del_n(self, n):
        self._dfmixin_df = self.df()
        self._dfmixin_df = self._dfmixin_df.drop(index=sorted(self._dfmixin_df.index)[-n:])
        self.to_feathre(self.df_file)

    def df(self):
        if self.cache_df is not None:
            return self.cache_df

        if self.df_file.exists():
            self._dfmixin_df = pd.read_feather(self.df_file)
            self._dfmixin_df.index = pd.DatetimeIndex(self._dfmixin_df['date'])
            del self._dfmixin_df['date']

            start = max(self._dfmixin_df.index)
        else:
            start = '1990-01-01'
            self._dfmixin_df = None

        dates = pd.date_range(start, datetime.datetime.now())
        dates = [d for d in dates if d.weekday() not in (5, 6)]

        print('from', min(dates), 'to', max(dates))
        if len(dates) > 2:
            df = self.down_load(dates)
            if self._dfmixin_df is not None:
                if df is not None:
                    self._dfmixin_df = self._dfmixin_df.drop(df.index, errors='ignore')
                self._dfmixin_df = pd.concat([self._dfmixin_df, df])
            else:
                self._dfmixin_df = df

            # self._dfmixin_df['date'] = self._dfmixin_df.index.strftime('%Y-%m-%d')
            # self._dfmixin_df.reset_index(inplace=True, drop=True)
            # self._dfmixin_df.to_feather(self.df_file)

            # self._dfmixin_df.index = pd.DatetimeIndex(self._dfmixin_df['date'])
            # del(self._dfmixin_df['date'])
            self.to_feathre(self.df_file)

        return self._dfmixin_df


class _ColIndexDfMixin(DfCacheMixin):
    index_col = 'code'
    diffdays = 5

    @property
    def df_file(self):
        raise NotImplementedError

    def down_load(self, dates, *args, **kwargs):
        raise NotImplementedError

    def handler_idx_col(self):
        self._dfmixin_df[self.index_col] = self._dfmixin_df[self.index_col].apply(lambda x: str(x).rjust(6, '0'))

    def to_feathre(self, df_file):
        self._dfmixin_df[self.index_col] = self._dfmixin_df.index
        self._dfmixin_df = handler(self._dfmixin_df)
        self.handler_idx_col()
        self._dfmixin_df.reset_index(inplace=True, drop=True)
        print(df_file, len(self._dfmixin_df))
        if not isinstance(df_file, pathlib.Path):
            _tmp = pathlib.Path(df_file + '.tmp')
        else:
            _tmp = pathlib.Path(str(df_file) + '.tmp')

        self._dfmixin_df.to_feather(_tmp)
        _tmp.rename(df_file)
        self._dfmixin_df.index = self._dfmixin_df.code
        del self._dfmixin_df[self.index_col]

    def _df(self):
        if self.cache_df is not None:
            return self.cache_df

        if self.df_file.exists():
            self._dfmixin_df = pd.read_feather(self.df_file)
            self._dfmixin_df.index = self._dfmixin_df[self.index_col]
            del self._dfmixin_df[self.index_col]
            start = datetime.datetime.fromtimestamp(self.df_file.stat().st_ctime)

        else:
            start = datetime.datetime(1700, 1, 1)
            self._dfmixin_df = None

        if (datetime.datetime.now() - start).days >= self.diffdays:
            self._dfmixin_df = self.down_load()

            self.to_feathre(self.df_file)

        self._dfmixin_df_time = time.time()
        return self._dfmixin_df

    def df(self):
        return self._df()


class CodeIndexDfMixin(_ColIndexDfMixin):
    index_col = 'code'
    diffdays = 5


class IndexDfMixin(_ColIndexDfMixin):
    index_col = 'idx'
    diffdays = 0

    def handler_idx_col(self):
        pass
    # @property
    # def df_file(self):
    #     raise NotImplementedError

    # def down_load(self, dates, *args, **kwargs):
    #     raise NotImplementedError

    # def to_feathre(self, df_file):
    #     self._dfmixin_df['code'] = self._dfmixin_df.index
    #     self._dfmixin_df = handler(self._dfmixin_df)
    #     self._dfmixin_df['code'] = self._dfmixin_df['code'].apply(lambda x: str(x).rjust(6, '0'))
    #     self._dfmixin_df.reset_index(inplace=True, drop=True)
    #     print(df_file)
    #     if not isinstance(df_file, pathlib.Path):
    #         _tmp = pathlib.Path(df_file + '.tmp')
    #     else:
    #         _tmp = pathlib.Path(str(df_file) + '.tmp')

    #     self._dfmixin_df.to_feather(_tmp)
    #     _tmp.rename(df_file)
    #     self._dfmixin_df.index = self._dfmixin_df.code
    #     del self._dfmixin_df['code']

    # def df(self):
    #     if self.cache_df is not None:
    #         return self.cache_df

    #     if self.df_file.exists():
    #         self._dfmixin_df = pd.read_feather(self.df_file)
    #         self._dfmixin_df.index = self._dfmixin_df['code']
    #         del self._dfmixin_df['code']
    #         start = datetime.datetime.fromtimestamp(self.df_file.stat().st_ctime)

    #     else:
    #         start = datetime.datetime(1700, 1, 1)
    #         self._dfmixin_df = None

    #     if (datetime.datetime.now() - start).days > 5:
    #         self._dfmixin_df = self.down_load()

    #         self.to_feathre(self.df_file)

    #     self._dfmixin_df_time = time.time()
    #     return self._dfmixin_df
