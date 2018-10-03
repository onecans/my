import pickle
import zlib
from collections import defaultdict

import pandas as pd
import plyvel

from mystockdata import config

LEVEL_DB_NAME = config.LEVEL_DB_NAME
LEVEL_DBS = {}


def force_bytes(s):
    try:
        return s.encode()
    except:
        return s


def force_unicode(s):
    try:
        return s.decode()
    except:
        return s


class Db:
    name = LEVEL_DB_NAME

    def __init__(self,  **kwargs):
        global LEVEL_DB
        if not self.name in LEVEL_DBS:
            LEVEL_DBS[self.name] = plyvel.DB(
                self.name, create_if_missing=True, ** kwargs)
        self.db = LEVEL_DBS[self.name]

    def close(self):
        del LEVEL_DBS[self.name]
        if isinstance(self.db, plyvel.DB):
            self.db.close()
        else:
            self.db.db.close()

    def keys(self):
        return self.db.iterator(include_value=False)

    def values(self):
        return self.db.iterator(include_key=False)

    def items(self):
        return self.db.iterator()


class PrefixedDb(Db):
    prefix = ''

    def __init__(self,  **kwargs):
        super().__init__(**kwargs)
        if self.prefix:
            self.db = self.db.prefixed_db(force_bytes(self.prefix))
        else:
            raise ValueError('prefix can not be none')


class DfIndexDb(Db):

    def pre_save(self, df):
        pass

    def save(self, df):
        self.pre_save(df)
        with self.db.write_batch() as wb:
            for column in df.columns:
                v = df[column]
                self.db.put(column.encode(),
                            pickle.dumps(v))
            # self.db.put(force_bytes(self.index_col), pickle.dumps(df.index))

    def delete(self, columns=None):
        with self.db.write_batch() as wb:
            for column in columns if columns else self.keys():
                self.db.delete(force_bytes(column))

    def read(self, columns=None):
        _columns = columns if columns else self.keys()
        serieses = list()

        for c in _columns:
            v = pickle.loads(
                self.db.get(force_bytes(c)))
            serieses.append(v)
        if serieses:
            df = pd.concat(serieses, axis=1)
            df = self.handler_result(df)
            return df
        else:
            return None

    def handler_result(self, df):
        return df


class DfDb(Db):
    index_col = 'index'

    def pre_save(self, df):
        return df

    def saved_index(self):
        v = self.db.get(force_bytes(self.index_col))
        if v:
            return pickle.loads(v)
        else:
            return None

    def save(self, df):
        df = self.pre_save(df)
        with self.db.write_batch() as wb:
            for column in df.columns:
                v = df[column]
                self.db.put(column.encode(),
                            pickle.dumps(v.values))
            self.db.put(force_bytes(self.index_col), pickle.dumps(df.index))

    def delete(self, columns=None):
        with self.db.write_batch() as wb:
            for column in columns if columns else self.keys():
                self.db.delete(force_bytes(column))
            if columns is None:
                self.db.delete(force_bytes(self.index_col))

    def read(self, columns=None):
        _columns = columns if columns else self.keys()
        serieses = list()
        tmp = dict()
        for c in _columns:
            if c == self.index_col:
                continue
            try:
                v = pickle.loads(
                    self.db.get(force_bytes(c)))
            except TypeError:
                print('try to get %s error' % c)
                raise

            tmp[force_unicode(c)] = v
        index = pickle.loads(self.db.get(force_bytes(self.index_col)))
        if tmp:
            df = pd.DataFrame(data=tmp, index=index)
            df = self.handler_result(df)

            return df
        else:
            return None

    def handler_result(self, df):
        return df


class DatetimeIndexMixin:
    def handler_result(self, df):
        # df = df.sort_index()
        # df = df.reindex(pd.date_range(
        #     min(df.index), max(df.index)), method='ffill')
        # df = df.reindex(pd.date_range(
        #     min(df.index), max(df.index)), method='bfill')
        # df = df.fillna(method='ffill')
        # df = df.fillna(method='bfill')
        return df

    def pre_save(self, df):
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.DatetimeIndex(df.index)

        saved_index = self.saved_index()
        if saved_index is not None:
            if min(df.index) < min(saved_index) or max(df.index) > max(saved_index):
                tmp = self.read()
                tmp = tmp[[c for c in tmp.columns if c not in df.columns]]

                df = pd.concat([tmp, df], axis=1)
                dates = pd.date_range(min(df.index), max(df.index))
            else:
                dates = pd.date_range(min(saved_index), max(saved_index))
        else:
            dates = pd.date_range(min(df.index), max(df.index))
        df = df.sort_index()
        df = df.reindex(dates, method='ffill')
        df = df.fillna(method='ffill')
        df = df.fillna(method='bfill')
        return df


class PrefixedDfDb(DfDb):
    prefix = ''

    def __init__(self,  **kwargs):
        super().__init__(**kwargs)
        if self.prefix:
            self.db = self.db.prefixed_db(force_bytes(self.prefix))
        else:
            raise ValueError('prefix can not be none')


def main():
    global LEVEL_DB_NAME
    LEVEL_DB_NAME = '/tmp/test'
    import pandas as pd
    import datetime
    df = pd.DataFrame(data={'A': ['x', 'y'], 'B': [1, 2], 'C': [
        datetime.datetime.now(), datetime.datetime.now()]}, index=[
        datetime.datetime.now(), datetime.datetime.now()])

    TestDb = PrefixedDfDb
    TestDb.prefix = 'test'
    db = TestDb()
    db.save(df)
    for x in db.keys():
        print(x)

    # for y in db.values():
    #     print(y)

    print(db.read())
    print(db.read(['A']))
    db.delete(columns=['A'])

    for y in db.keys():
        print(y)

    print('delete')
    db.delete()
    for y in db.keys():
        print(y)

    db.close()


if __name__ == '__main__':
    main()
