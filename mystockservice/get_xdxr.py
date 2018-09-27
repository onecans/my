from pytdx.util.best_ip import select_best_ip

from pytdx.hq import TdxHq_API

import pandas as pd
import time
def _select_market_code(code):
    """
    1- sh
    0 -sz
    """
    code = str(code)
    if code[0] in ['5', '6', '9'] or code[:3] in ["009", "126", "110", "201", "202", "203", "204"]:
        return 1
    return 0


def QA_fetch_get_stock_xdxr(code, ip=None, port=None):
    '除权除息'
    # ip = select_best_ip()
    ip = '202.108.253.130'
    print(ip)
    api = TdxHq_API()
    market_code = _select_market_code(code)
    s = time.time()
    with api.connect(ip):
        category = {
            '1': '除权除息', '2': '送配股上市', '3': '非流通股上市', '4': '未知股本变动', '5': '股本变化',
            '6': '增发新股', '7': '股份回购', '8': '增发新股上市', '9': '转配股上市', '10': '可转债上市',
            '11': '扩缩股', '12': '非流通股缩股', '13':  '送认购权证', '14': '送认沽权证'}
        data = api.to_df(api.get_xdxr_info(market_code, code))
        if len(data) >= 1:
            data = data\
                .assign(date=pd.to_datetime(data[['year', 'month', 'day']]))\
                .drop(['year', 'month', 'day'], axis=1)\
                .assign(category_meaning=data['category'].apply(lambda x: category[str(x)]))\
                .assign(code=str(code))\
                .rename(index=str, columns={'panhouliutong': 'liquidity_after',
                                            'panqianliutong': 'liquidity_before', 'houzongguben': 'shares_after',
                                            'qianzongguben': 'shares_before'})\
                .set_index('date', drop=False, inplace=False)
            return data.assign(date=data['date'].apply(lambda x: str(x)[0:10]))
        else:
            return None

        e = time.time()

    
    print('using time', e-s)



df =QA_fetch_get_stock_xdxr('000001')

print(df[['code','date','category','name','fenhong','liquidity_before', 'liquidity_after', 'shares_before',
       'shares_after']])
print(df.columns)