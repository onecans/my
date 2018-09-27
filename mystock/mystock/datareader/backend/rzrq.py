import datetime
import json
import pathlib
import time

import pandas as pd
import requests

from .base import DfMixin


class RZRQ(DfMixin):
    file_path = '/data/stock/rzrq'

    def __init__(self, code, index=False):
        self.code = code
        self.index = index

    def down_load(self, dates):
        def _fetch(code, index, page_num):
            s = None
            if not index:
                url = ('http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get?type=RZRQ_DETAIL_NJ&',
                       'token=70f12f2f4f091e459a279469fe49eca5&filter=(scode=%27[CODE]%27)&st=tdate&sr=-1&p=*****&'.replace(
                           '[CODE]', code),
                       'ps=50&js=var%20erHHrlfD={pages:(tp),data:(x)}&time=1&rt=50675219')
            else:
                if code == '000001':
                    url = ('http://dcfm.eastmoney.com//EM_MutiSvcExpandInterface/api/js/get?',
                           'token=70f12f2f4f091e459a279469fe49eca5&st=tdate&sr=-1&p=*****&ps=50&',
                           'js=var%20quzXmkEC={pages:(tp),data:%20(x)}&type=RZRQ_HSTOTAL_NJ&filter=(market=%27SH%27)&mk_time=1&rt=50706413')
                elif code == '399001':
                    url = ('http://dcfm.eastmoney.com//EM_MutiSvcExpandInterface/api/js/get?',
                           'token=70f12f2f4f091e459a279469fe49eca5&st=tdate&sr=-1&p=*****&ps=50&',
                           'js=var%20quzXmkEC={pages:(tp),data:%20(x)}&type=RZRQ_HSTOTAL_NJ&filter=(market=%27SZ%27)&mk_time=1&rt=50706413')

            while True:
                if s is None:
                    s = requests.Session()
                try:
                    url = ''.join(url).replace('*****', str(page_num))
                    r = s.get(url)
                    t = r.text[28:-1]
                    print(page_num, t[:50])

                    j = json.loads(t)
                    df = pd.DataFrame.from_dict(j)
                    break
                except Exception as e:
                    print(e.args)
                    print('sleep...')
                    time.sleep(60)
                    s = requests.Session()

            if not df.empty:
                df.index = pd.DatetimeIndex(df.tdate)
                df = df[['rzye', ]]
            return df

        page_num = 1
        df = None
        while page_num <= 100:
            tmp = _fetch(self.code, self.index, page_num)
            if tmp.empty:
                break

            if df is None:
                df = tmp
            else:
                df = pd.concat([df, tmp])

            print(min(df.index), 'to', max(df.index))

            if min(df.index) <= min(dates):
                break
            else:
                time.sleep(1)

            page_num += 1

        return df

    @property
    def df_file(self):
        if self.index:
            return pathlib.Path(self.file_path) / f'index_{self.code}'
        else:
            return pathlib.Path(self.file_path) / f'{self.code}'
