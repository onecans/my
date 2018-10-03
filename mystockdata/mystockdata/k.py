import pathlib

import pandas as pd

from mystockdata import code_base
from mystockdata.config import BFQ_FILE_PATH, QFQ_FILE_PATH


def sync_code(code, force=False):
    codedb = code_base.CodeDb(code=code)
    if not force:
        exists = False
        for key in codedb.keys():
            exists = True
            break

        if exists:
            return

    columns = ['date', 'open', 'high',
               'low', 'close', 'volume', 'amount']
    k_file_path = pathlib.Path(QFQ_FILE_PATH)
    bfq_k_file_path = pathlib.Path(BFQ_FILE_PATH)
    in_sh = in_sz = False
    if (k_file_path / f'SH#{code}.txt').exists():
        file_name = f'SH#{code}.txt'
        in_sh = True
    elif (k_file_path / f'SZ#{code}.txt').exists():
        file_name = f'SZ#{code}.txt'
        in_sz = True
    else:
        print(f'{code}: not found file')
        return

    if in_sh and in_sz:
        print(f'code, {code} error, 存在于两个市场')

    tmp = pd.read_csv(k_file_path/file_name, skiprows=1, engine='python',
                      encoding='gbk', sep='\t', skipfooter=1)
    # if index:
    #     tmp.drop(tmp.columns[6:], axis=1, inplace=True)
    #     tmp[6] = 0
    # if not columns:
    #     raise web.HTTPInternalServerError()
    tmp.columns = columns
    if 'date' in tmp.columns:
        tmp.index = pd.DatetimeIndex(tmp['date'])
        del tmp['date']
    if tmp.empty:
        return
    dates = pd.date_range(min(tmp.index), max(tmp.index))
    # 处理bfq
    if pathlib.Path(bfq_k_file_path/file_name).exists():
        bfq = pd.read_csv(bfq_k_file_path/file_name, skiprows=1,
                          engine='python', encoding='gbk', sep='\t', skipfooter=1)
        bfq.columns = ['bfq_' + c for c in columns]
        if 'bfq_date' in bfq.columns:
            bfq.index = pd.DatetimeIndex(bfq['bfq_date'])
            del bfq['bfq_date']
            del bfq['bfq_volume']
            del bfq['bfq_amount']
        if sum(tmp.index.duplicated(keep=False)):
            tmp = tmp.groupby(tmp.index).min()
        if sum(bfq.index.duplicated(keep=False)):
            bfq = bfq.groupby(bfq.index).min()
        tmp = tmp.reindex(
            dates, method='ffill')
        bfq = bfq.reindex(dates, method='ffill')

        tmp = pd.concat([tmp, bfq], axis=1, join='inner')

    codedb.save(tmp)
