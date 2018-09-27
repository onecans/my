
import pathlib
import zipfile
from collections import namedtuple
from hashlib import md5
from struct import *

import requests
from pytdx.reader.history_financial_reader import HistoryFinancialReader

# def _files():
#     files = requests.get('http://down.tdx.com.cn:8001/fin/gpcw.txt').text.split()
# #     files = [FinFile(*f.split(',')) for f in files]
#     return [f.split(',') for f in files]


# current_files = _files()


def get_file(year, quarter):
    _format = 'gpcw{year}{md}.zip'
    if quarter == 1:
        file_name = _format.format(year=year, md='0331')
    if quarter == 2:
        file_name = _format.format(year=year, md='0631')
    if quarter == 3:
        file_name = _format.format(year=year, md='0930')
    if quarter == 4:
        file_name = _format.format(year=year, md='1231')

    return [f for f in current_files if f[0] == file_name][0]


class FinFile:
    file_path = '/data/stock/tdx/finzips/'

    def __init__(self, file_name, md5, size):
        self.file_name = file_name
        self.md5 = md5
        self.size = size

    @property
    def down_url(self):
        return 'http://down.tdx.com.cn:8001/fin/{file_name}'.format(file_name=self.file_name)

    @property
    def cache_file_name(self):
        return self.file_path + self.file_name

    @property
    def cache_file_md5(self):
        if not pathlib.Path(self.cache_file_name).exists():
            return 'x'
        m = md5()
        with open(self.cache_file_name, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    def _down_load(self):
        print(f'down {self.down_url} ==> {self.cache_file_name}')
        r = requests.get(self.down_url, stream=True)
        with open(self.cache_file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        zip_file = zipfile.ZipFile(self.cache_file_name)
        zip_file.extractall(path=self.file_path)

    def __enter__(self):
        for f in current_files:
            if f[0] == self.file_name:
                if f[1] != self.cache_file_md5:
                    self._down_load()

        return self

    def __exit__(self, exc_type, exc, trace_info):
        pass

    def to_df(self):
        datafile = self.cache_file_name.replace('.zip', '.dat')
        df = HistoryFinancialReader().get_df(datafile)
        return df


def get_fin(year, quarter):
    f = get_file(year, quarter)
    with FinFile(*f) as f1:
        return f1.to_df()
