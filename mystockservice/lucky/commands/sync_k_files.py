import concurrent
import os
import pathlib
import urllib
from concurrent import futures

import requests
import tushare as ts
import yaml

PROJ_ROOT = pathlib.Path(__file__).parent.parent.parent.absolute()
URL = 'http://localhost:9001/'


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    # TODO: add config validation
    return data


def sync_file():
    config = load_config(PROJ_ROOT / 'config' / 'config.yml')
    for root, dirs, files in os.walk(config['k_file_path']):
        with futures.ThreadPoolExecutor(max_workers=10) as pool:
            rst = []
            i = 0
            for file in files:
                if not file.endswith('.txt'):
                    continue
                i += 1
                if file.startswith('SH') or file.startswith('SZ'):
                    # continue
                    # if file != 'SH#999999.txt':
                    #     continue
                    url = URL + 'upload/' + urllib.parse.quote(file)
                    # if i < 10
                    rst.append(pool.submit(requests.post, url))
                elif file[0] in ('0', '3'):
                    url = URL + 'uploadidx/' + urllib.parse.quote(file)
                    rst.append(pool.submit(requests.post, url))
                else:
                    url = URL + 'uploadother/' + urllib.parse.quote(file)
                    rst.append(pool.submit(requests.post, url))

        for rec in rst:
            r = rec.result()
            if r.status_code != 200:
                print(r.text)


def sync_base():
    # base = ts.get_stock_basics()
    r = requests.post(URL + 'baseinfo')
    print(r.text)


if __name__ == '__main__':
    sync_file()
    sync_base()
