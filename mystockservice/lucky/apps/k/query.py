from collections import Counter
from functools import wraps

import pandas as pd

from lucky.apps import backends


def valid(d):

    def wrap(func):
        @wraps(func)
        def _wrap(*args, **kwargs):
            for key, value in d.items():
                if key in kwargs:
                    if kwargs[key] not in value:
                        raise KeyError(
                            'Parameter {key} must be one of {value}'.format(**locals()))
            rst = func(*args, **kwargs)
            return rst
        return _wrap

    return wrap


def mandatory_cols(cols):
    def wrap(func):
        @wraps(func)
        def _wrap(self, *args, **kwargs):
            if self.df is None:
                raise ValueError('df can not be None')
            for col in cols:
                if col not in self.df.columns:
                    raise ValueError(
                        '{col} must be in df columns'.format(**locals()))

            return func(self, *args, **kwargs)
        return _wrap
    return wrap


async def cache_df(expires):
    async def wrap(func):
        @wraps(func)
        async def _wrap(self, app=None):
            if app is not None:
                self.app = app

            if self.app is None:
                raise ValueError('app can not be None')

        return _wrap
    return wrap


async def _to_df(paras):
    codes = paras.code.split(',')
    df = await loads_keys(paras.app, [paras.col, ], codes=codes, where=paras.where, to_df=True)
    tmp = {}
    if not df.empty:
        df = _filter_df(df, paras)

    return df


async def _line(paras):
    df = await _to_df(paras)

    df = df.dropna(how='all')

    start = paras.start if paras.start != 'start' else min(df.index)
    end = paras.end if paras.end != 'end' else max(df.index)
    ds = pd.date_range(start, end)
    df = df.reindex(ds, method='bfill',
                    copy=False, fill_value=np.NaN)

    return df[paras.col]


class Line:
    @valid({'where': ['SH', 'SZ', 'INDEX', 'ALL']})
    def __init__(self, *, code, where='ALL', col='high', start='start', end='end', app=None, nocache=False):
        self.code = code
        self.where = where
        self.start = 'start'
        self.end = 'end'
        self.cols = None
        self.nocache = nocache

        self.date_range(start, end)
        if col:
            self.col(col)
        self.app(app)

    def date_range(self, start, end):
        self.start = start
        self.end = end
        return self

    def col(self, col):
        self.cols = col.split(',')
        return self

    def app(self, app):
        self.app = app
        return self

    def __str__(self):
        return '{self.code}:{self.cols}@[{self.start}-{self.end}]/{self.app}.format(**locals())'

    # @cache_df(expires=12*60*60)
    async def _to_df(self, app=None):
        if app:
            self.app = app

        if self.app is None:
            raise ValueError('app can not be None')
        if self.code is None:
            raise ValueError('app can not be None')
        if self.col is None:
            raise ValueError('col can not be None')

        df = await backends.code_info(self.app, columns=self.cols, code=self.code)

        return df

    async def to_df(self, app=None):
        if app:
            self.app = app

        df = await self._to_df()
        if not df.empty:
            if self.start and self.start != 'start':
                df = df[df.index >= self.start]
            if self.end and self.end != 'end':
                df = df[df.index <= self.end]

        return LineDf(df)


class LineDf:

    def __init__(self, df):
        self.df = df
        self.current_col = df.columns[0]

    # def col(self, *, col):
    #     self.cols = col.split(',')
    #     self.df = df[self.cols]
    #     return self

    def current_col(self, col):
        self.current_col = col

    def top_k(self, col=None, k=10):
        if col is not None:
            self.current_col = col

        self.df = self.df.sort_values(col, ascending=True).tail(k)
        return self

    def min_k(self, col=None, k=10):
        if col is not None:
            self.current_col = col

        self.df = self.df.sort_values(
            self.current_col, ascending=False).tail(k)
        return self

    def is_min(self, k=90):
        min_date = df.idxmin()
        if min_date in self.df.index[: -k]:
            return True
        else:
            return False

    def is_max(self, k=90):
        min_date = df.idxmax()
        if min_date in self.df.index[: -k]:
            return True
        else:
            return False

    @mandatory_cols(['high'])
    def max_count(self, window_size=30 * 52, resample=None):
        '''
        排查每一天，确认是否破新高
        '''
        col = 'high'
        self.df = self.df\
            .assign(cummax=self.df[col].cummax())
        self.df = self.df\
            .assign(ismax=self.df[col] == self.df['cummax'])\
            .assign(rolling_max=self.df[col].rolling(window_size).max())

        self.df = self.df\
            .assign(is_rolling_max=self.df[col] == self.df['rolling_max'])\

        counters = {}
        for _col in ['is_rolling_max', 'ismax']:
            tmp = self.df[[_col]]
            if resample:
                tmp = tmp.resample(resample).sum()
                tmp = tmp > 0

            tmp = tmp[tmp.sum(axis=1) > 0]
            tmp.index = tmp.index.strftime('%Y-%m-%d')
            c = Counter()
            c.update(**tmp.to_dict()[_col])
            counters[_col] = c

        return counters

    @mandatory_cols(['low'])
    def min_count(self, window_size=30 * 52, resample=None):
        '''
        排查每一天，确认是否破新低
        '''
        col = 'low'
        self.df = self.df\
            .assign(cummin=self.df[col].cummin())
        self.df = self.df\
            .assign(ismin=self.df[col] == self.df['cummin'])\
            .assign(rolling_min=self.df[col].rolling(window_size).min())

        self.df = self.df\
            .assign(is_rolling_min=self.df[col] == self.df['rolling_min'])

        counters = {}
        for _col in ['is_rolling_min', 'ismin', ]:
            tmp = self.df[[_col]]
            if resample:
                tmp = tmp.resample(resample).sum()
                tmp = tmp > 0

            tmp = tmp[tmp.sum(axis=1) > 0]
            tmp.index = tmp.index.strftime('%Y-%m-%d')
            c = Counter()
            c.update(**tmp.to_dict()[_col])
            counters[_col] = c

        return counters

    def to_dict(self, inplace=False):
        if inplace:
            tmp = self.df
        else:
            tmp = self.df.copy()

        tmp.index = self.df.index.strftime('%Y-%m-%d')
        tmp.index = self.df.index.strftime('%Y-%m-%d')

        return tmp.to_dict()

    @mandatory_cols(['low', 'high'])
    def range(self, start1, end1, start2, end2):
        # 最高点到最低点
        rst = {}
        # print(self.df)
        if self.df is not None and not self.df.empty:
            start_df = self.df[self.df.index >= start1].copy()
            start_df = start_df[start_df.index <= end1]
            end_df = self.df[self.df.index >= start2].copy()
            end_df = end_df[end_df.index <= end2]

            if start_df.empty or end_df.empty:
                return {'loser': {'range': 999999}, 'winer': {'range': 999999}}

            start_high_idx = start_df['high'].idxmax()
            start_low_idx = start_df['low'].idxmin()

            end_high_idx = end_df['high'].idxmax()
            end_low_idx = end_df['low'].idxmin()

            start_high, start_low, end_high, end_low = (start_df['high'].loc[start_high_idx],
                                                        start_df['low'].loc[start_low_idx],
                                                        end_df['high'].loc[end_high_idx],
                                                        end_df['low'].loc[end_high_idx],)

            # for 跌幅
            range1 = (end_low - start_high)/start_high
            rst['loser'] = {
                'start': start_high,
                'start_date': start_high_idx.strftime('%Y-%m-%d'),
                'end': end_low,
                'end_date': end_low_idx.strftime('%Y-%m-%d'), 'range': start_high / end_low,
                'math_range': range1}

            # for 涨幅
            range2 = (end_high - start_low) / start_low
            rst['winer'] = {
                'start': start_low,
                'start_date': start_low_idx.strftime('%Y-%m-%d'),
                'end': end_high,
                'end_date': end_high_idx.strftime('%Y-%m-%d'), 'range': end_high / start_low,
                'math_range': range2}
            return rst
        else:
            return {'loser': {'range': 999999}, 'winer': {'range': 999999}}


def main():
    q = Query()
    return q.where(where='a')


if __name__ == '__main__':
    main()
