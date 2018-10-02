import pathlib
import time
from collections import Counter

import pandas as pd
from pytdx.hq import TdxHq_API
from pytdx.util.best_ip import select_best_ip

from mystockdata import _pytdx, code_base, db
from mystockdata.config import XDXR_FILE_PATH

# df =QA_fetch_get_stock_xdxr('000001')

# print(df[['code','date','category','name','fenhong','liquidity_before', 'liquidity_after', 'shares_before',
#        'shares_after']])
# print(df.columns)


# def download(code=None, from_tdx=False):
#     get_ip()
#     p = pathlib.Path(XDXR_FILE_PATH)
#     df = QA_fetch_get_stock_list()
#     c = Counter()
#     for code in df['code']:
#         download(code, from_tdx=False)


def download_code(code, from_tdx=False):
    p = pathlib.Path(XDXR_FILE_PATH)

    _path = p / ('%s.csv' % code)
    if _path.exists() and not from_tdx:
        xdxr = pd.read_csv(_path)
    else:
        xdxr = _pytdx.QA_fetch_get_stock_xdxr(code)
        if xdxr is not None:
            error_codes.append(code)
            xdxr.to_csv(_path)
    if xdxr is None:
        return 'No data found'
    else:
        xdxr.index = pd.DatetimeIndex(xdxr.date)

        xdxr = xdxr[xdxr['category'] != 6]  # 去除 6-增发新股

        df1 = xdxr[['shares_before']].dropna()
        df2 = xdxr[['shares_after']].dropna()
        df3 = xdxr[['liquidity_before']].dropna()
        df4 = xdxr[['liquidity_after']].dropna()

        if sum(df1.index.duplicated(keep=False)):
            df1 = df1.groupby(df1.index).min()

        if sum(df2.index.duplicated(keep=False)):
            df2 = df2.groupby(df2.index).max()

        if sum(df3.index.duplicated(keep=False)):
            df3 = df3.groupby(df3.index).min()

        if sum(df4.index.duplicated(keep=False)):
            df4 = df4.groupby(df4.index).max()

        # df1 = df1.reindex(dates, method='bfill')
        # df2 = df2.reindex(dates, method='ffill')
        # df3 = df3.reindex(dates, method='bfill')
        # df4 = df4.reindex(dates, method='ffill')

        xdxr = pd.concat([df1, df2, df3, df4], axis=1).fillna(0)

        xdxr['shares'] = xdxr[['shares_before',
                               'shares_after']].apply(max, axis=1)
        xdxr['liquidity'] = xdxr[['liquidity_before',
                                  'liquidity_after']].apply(max, axis=1)

        xdxr = xdxr[['shares', 'liquidity']]

        code_db = code_base.CodeDb(code=code)
        code_db.save(xdxr)
