# encoding=utf-8


import codecs
import datetime
import locale
import os
import time
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

from .settings import CACHE_DIR
HEADER = '排名,股东名称,持股数量(股),占总股本比例,与上期持股变化(股),股份类型,股东性质'

month = datetime.datetime.today().strftime('%Y%m')
CACHE_FILE = os.path.join(CACHE_DIR, 'sdgd.' + month)

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def get_sdgd(code):
    try:

        _code = str(code).rjust(6, '0')
        url = 'http://stock.jrj.com.cn/share,%s,sdgd.shtml' % _code
        print (url)
        response = requests.get(url)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, "lxml")
        tables = soup.find("table", {"class": "tab1"})
        records = []
        for row in tables.findAll('tr'):
            col = [i.string for i in row.findAll('td')]
            if col:
                print (col)
                record = OrderedDict()
                record['fetch_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                record['code'] = _code
                record['seq'] = int(col[0])
                record['name'] = unicode(col[1])
                record['cnt'] = locale.atof(col[2])
                record['proportion'] = float(col[3].replace('%', '')) / 100 if col[3] else 0
                record['update'] = locale.atof(col[4]) if col[4] else 0
                record['gd_type'] = unicode(col[5])
                record['owner_type'] = unicode(col[6])
                records.append(record)

        # text = u'\r\n'.join(records)
        return records
    except:
        raise


#
# def get_sdgd(code):
#     if not os.path.exists(CACHE_FILE):
#         sdgd = _get_sdgd(code)
#         df = pd.read_csv(sdgd)
#         df.to_csv(CACHE_FILE, encoding='utf-8')
#         return df[df['code'] == code]
#
#     df = pd.read_csv(CACHE_FILE)
#
#
#     stock_basics = pd.read_csv(CACHE_FILE)
#     stock_basics = stock_basics.set_index('code')

if __name__ == '__main__':
    texts = list()
    for code in ('1', '2'):
        texts.append(get_sdgd(code))
        time.sleep(1)

    fl = codecs.open('output.txt', 'wb', 'utf-8')
    fl.write(u'\r\n'.join(texts))
    fl.close()
