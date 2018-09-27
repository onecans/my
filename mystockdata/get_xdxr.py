from pytdx.util.best_ip import select_best_ip

from pytdx.hq import TdxHq_API

import pandas as pd
import time

ip = select_best_ip()
ip = '180.153.18.170'
# ip = '202.108.253.130'
print(ip)
def _select_market_code(code):
    """
    1- sh
    0 -sz
    """
    code = str(code)
    if code[0] in ['5', '6', '9'] or code[:3] in ["009", "126", "110", "201", "202", "203", "204"]:
        return 1
    return 0

def _codes():
    
    api = TdxHq_API()
    
    with api.connect(ip):
        rst=api.get_security_list(0,255)

    return rst

def QA_fetch_get_stock_xdxr(code):
    '除权除息'
    api = TdxHq_API()
    market_code = _select_market_code(code)
    s = time.time()
    print(ip)
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


def for_sz(code):
    """深市代码分类

    Arguments:
        code {[type]} -- [description]

    Returns:
        [type] -- [description]
    """

    if str(code)[0:2] in ['00', '30', '02']:
        return 'stock_cn'
    elif str(code)[0:2] in ['39']:
        return 'index_cn'
    elif str(code)[0:2] in ['15']:
        return 'etf_cn'
    elif str(code)[0:2] in ['10', '11', '12', '13']:
        # 10xxxx 国债现货
        # 11xxxx 债券
        # 12xxxx 可转换债券
        # 12xxxx 国债回购
        return 'bond_cn'

    elif str(code)[0:2] in ['20']:
        return 'stockB_cn'
    else:
        return 'undefined'


def for_sh(code):
    if str(code)[0] == '6':
        return 'stock_cn'
    elif str(code)[0:3] in ['000', '880']:
        return 'index_cn'
    elif str(code)[0:2] == '51':
        return 'etf_cn'
    # 110×××120×××企业债券；
    # 129×××100×××可转换债券；
    elif str(code)[0:3] in ['129', '100', '110', '120']:
        return 'bond_cn'
    else:
        return 'undefined'

def QA_fetch_get_stock_list(type_='stock'):
    
    api = TdxHq_API()
    with api.connect(ip):
        data = pd.concat([pd.concat([api.to_df(api.get_security_list(j, i * 1000)).assign(sse='sz' if j == 0 else 'sh').set_index(
            ['code', 'sse'], drop=False) for i in range(int(api.get_security_count(j) / 1000) + 1)], axis=0) for j in range(2)], axis=0)
        #data.code = data.code.apply(int)
        sz = data.query('sse=="sz"')
        sh = data.query('sse=="sh"')

        sz = sz.assign(sec=sz.code.apply(for_sz))
        sh = sh.assign(sec=sh.code.apply(for_sh))

        if type_ in ['stock', 'gp']:

            return pd.concat([sz, sh]).query('sec=="stock_cn"').sort_index().assign(name=data['name'].apply(lambda x: str(x)[0:6]))

        elif type_ in ['index', 'zs']:

            return pd.concat([sz, sh]).query('sec=="index_cn"').sort_index().assign(name=data['name'].apply(lambda x: str(x)[0:6]))
            # .assign(szm=data['name'].apply(lambda x: ''.join([y[0] for y in lazy_pinyin(x)])))\
            # .assign(quanpin=data['name'].apply(lambda x: ''.join(lazy_pinyin(x))))
        elif type_ in ['etf', 'ETF']:
            return pd.concat([sz, sh]).query('sec=="etf_cn"').sort_index().assign(name=data['name'].apply(lambda x: str(x)[0:6]))

        else:
            return data.assign(code=data['code'].apply(lambda x: str(x))).assign(name=data['name'].apply(lambda x: str(x)[0:6]))
            # .assign(szm=data['name'].apply(lambda x: ''.join([y[0] for y in lazy_pinyin(x)])))\
            #    .assign(quanpin=data['name'].apply(lambda x: ''.join(lazy_pinyin(x))))


# df =QA_fetch_get_stock_xdxr('000001')

# print(df[['code','date','category','name','fenhong','liquidity_before', 'liquidity_after', 'shares_before',
#        'shares_after']])
# print(df.columns)



import pathlib
df= QA_fetch_get_stock_list()
for code in df['code']:
    print(code)
    if pathlib.Path('./xdxr/%s.csv' % code).exists():
        print('pass')
        continue
    
    df =QA_fetch_get_stock_xdxr(code)
    if df is not None:
        df.to_csv('./xdxr/%s.csv' % code)
    


