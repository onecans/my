from django.core.management.base import BaseCommand

import copy
from collections import OrderedDict

import pandas as pd
from progressbar import Bar, Percentage, \
    ProgressBar
from contrib.tslib import *


logstash = get_logstash('price_update', type='price_update')


def get_price_update_list2(code, bdate, edate, amount_type, days=1,
                           percents=None,
                           begin_price_type='close', end_price_type='high'):
    """

    :param code: 代码
    :param bdate: 开始日期 '1997-05-12'
    :param edate: 结束日期 '1997-08-12'
    :param days: 计算开始价格,可以选取开始数天的某一个价格。
    :param percents: 统计比例,(-99999, -0.2, 0, 0.2, 9999)
    :param begin_price_type: 开始价格的类型 , close, open, high, low
    :param end_price_type: 结束价格的类型, close, open, high, low
    :param amount_type: 根据金额计算比重,一般为交易量 amount  股票数量 cnt
    :return: OrderDict
    """
    if not percents:
        percents = {'per': (-99999, -0.2, 0, 0.2, 9999)}

    _code = str(code).rjust(6, '0')

    df = get_qfq(code=_code, bdate=bdate, edate=edate)

    if df is None or df.empty or len(df) <= days + 1:
        return None

    begin_df = df.tail(days)
    begin_idx = begin_df.idxmin(axis=0)[begin_price_type]
    begin = begin_df.loc[begin_idx][begin_price_type]

    _bdate = df.index[-1 * (days + 1)]
    update_dict = OrderedDict()

    for d in pd.date_range(_bdate, edate):

        _data = dict()
        _date = d.strftime('%Y-%m-%d')

        try:
            end = df.loc[_date][end_price_type]
            amount = 100000000 if amount_type == 'cnt' else df.loc[_date][amount_type]
        except KeyError:
            continue

        update = (end - begin) / begin
        _data['update'] = update
        _data[amount_type] = amount

        ck = 0

        for per_name, _pers in percents.items():
            ck = 0
            for i in range(1, len(_pers)):
                _begin_per, _end_per = _pers[i - 1], _pers[i]
                # print _begin_per, _end_per
                if _begin_per < update <= _end_per:
                    _data[per_name] = '%s ~~ %s' % (_begin_per, _end_per)
                    ck += 1
                    # print code, _date, _data[per_name]

            if ck != 1:
                raise Exception('Error handler')

        _data['C' + amount_type] = (amount) / 100000000.0

        update_dict[_date] = _data
    return update_dict


class Command(BaseCommand):
    help = "fetch_upd_date_to_logstash"

    def handle(self, *args, **options):

        cals = list()
        # cal = {'START_DATE': '1997-05-12', 'END_DATE': '1998-08-30',
        #        'PERCENT': {'per': (-99999, -0.4, -0.2, 0, 0.2, 0.4, 9999)}, 'AMOUNT_TYPE': 'amount'}
        #
        # cals.append(cal)
        #
        
        cal = {'START_DATE': '1997-05-12', 'END_DATE': '1998-06-05',
               'PERCENT': {'per': (-99999, -0.6, -0.3, 0, 0.3, 0.6, 9999)}, 'AMOUNT_TYPE': 'cnt'}
        
        cals.append(cal) 
      
        cal = {'START_DATE': '1997-05-12', 'END_DATE': '1998-08-30',
               'PERCENT': {'per': (-99999, -0.6, -0.3, 0, 0.3, 0.6, 9999)}, 'AMOUNT_TYPE': 'cnt'}
        
        cals.append(cal)



        #
        # cal = {'START_DATE': '1997-09-23', 'END_DATE': '1998-08-30',
        #        'PERCENT': {'per': (-99999, 0.1, 0.2, 0.4, 0.6, 9999)}, 'AMOUNT_TYPE': 'cnt'}
        #
        # cals.append(cal)
        #

        # cal = {'START_DATE': '1997-09-23', 'END_DATE': '1998-08-30',
        #        'PERCENT': {'per': (-99999, 0.1, 0.2, 0.4, 0.6, 9999)}, 'AMOUNT_TYPE': 'amount'}

        # cal = {'START_DATE': '2015-12-23', 'END_DATE': '2017-10-31',
        #        'PERCENT': {'per': (-9999, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 9999)}, 'AMOUNT_TYPE': 'cnt'}

        
        cal = {'START_DATE': '2015-12-23', 'END_DATE': '2017-12-30',
               'PERCENT': {'per': (-9999, -0.6, -0.3, 0, 0.3, 0.6, 9999)}, 'AMOUNT_TYPE': 'cnt'}
        cals.append(cal)
        # cals.append(cal)

        cal = {'START_DATE': '2015-06-12', 'END_DATE': '2017-12-30',
               'PERCENT': {'per': (-99999, -0.6, -0.3, 0, 0.3, 0.6, 9999)}, 'AMOUNT_TYPE': 'cnt'}
        
        cals.append(cal) 

    
        default_extra = {
            'idx': 0,
            'code': 0,
            'cal_name': 'cal_name',
            'start_date': 'start_date',
            'end_date': 'end_date',
            'update': '0',
            'amount': 0,
            'C_amount': 0,
            'cnt': 0,
            'C_cnt': 0,
        }

        for cal in cals:
            start_date = cal['START_DATE']
            end_date = cal['END_DATE']
            amount_type = cal.get('AMOUNT_TYPE', 'amount')
            cal_name = start_date[2:].replace('-', '') + '_' + end_date[2:].replace('-', '')
            percent = cal['PERCENT']

            cnt = 0
            codes = get_sh_code_list()
            print ('begin cal_name:', cal_name)
            pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=len(codes)).start()
            for idx, code in enumerate(codes):
                # continue
                # print code
                try:
                    update = get_price_update_list2(code, bdate=start_date, edate=end_date, percents=percent,
                                                    amount_type=amount_type)
                    if update is None:
                        continue
                    for key, values in update.items():
                        extra = copy.copy(default_extra)
                        extra.update({
                            'idx': idx,
                            'code': parse_code(code),
                            'cal_name': cal_name,
                            'start_date': start_date,
                            'end_date': key
                        })
                        extra.update(values)
                        logstash.info(code, extra=extra)
                        cnt += 1
                except:
                    print ('ERROR %s' % code)
                    raise
                # print cal, cnt

                pbar.update(idx)
            pbar.finish()
            # 上海指数

        sh_df = get_qfq(code='000001', bdate=start_date, edate=end_date, index=True)
        for _date in sh_df.index:
            extra = copy.copy(default_extra)
            extra.update({
                'cal_name': cal_name,
                'start_date': start_date,
                'end_date': _date,
                'cnt': 0,
                'index_cnt': sh_df.loc[_date]['amount'] / 100000000,
                'index_close': sh_df.loc[_date]['close']
            })
            logstash.info('9000001', extra=extra)
