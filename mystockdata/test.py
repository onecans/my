# df1 = pd.concat([tmp, tmp2], axis=1)
# e = time.time()
# # print(df1)
# print(e-s)  # 0.04, 比leveldb 稍慢20%，数据量比leveldb 小 pass
import pickle
import time

import pandas as pd
import plyvel

from mystockdata.code_base import CodeDb, CodeIndexDb

# db = CodeIndexDb('601600')
# s = time.time()
# df = db.read()
# e = time.time()
# print(e-s)  # first 0.028


db = CodeDb('601600')
# db.save(df)

s = time.time()
df = db.read()
e = time.time()
print(e-s)

print(df.index)
# print(df.loc['2018-09-16'])
# s = time.time()
# columns = ['date', 'open', 'high',
#            'low', 'close', 'volume', 'amount']
# tmp = pd.read_csv('/u01/data/export/SH#601600.txt', skiprows=1, engine='python',
#                   encoding='gbk', sep='\t', skipfooter=1)
# tmp.columns = columns
# tmp.index = pd.DatetimeIndex(tmp['date'])

# tmp2 = pd.read_csv('/u01/data/export_bfq/SH#601600.txt', skiprows=1, engine='python',
#                    encoding='gbk', sep='\t', skipfooter=1)
# tmp2.columns = [c + '_bfq' for c in columns]
# tmp2.index = pd.DatetimeIndex(tmp2['date_bfq'])
# db = plyvel.DB('/tmp/test',  create_if_missing=True)

# s = time.time()

# with db.write_batch() as wb:
#     for column in df.columns:
#         v = df[column]
#         db.put(column.encode(),
#                pickle.dumps(v))
# e = time.time()  # 0.005

# print(e-s)


# s = time.time()

# with db.write_batch() as wb:
#     for column in df.columns:
#         v = df[column]
#         db.put(column.encode(),
#                pickle.dumps(v.tolist()))
#     db.put(b'index', pickle.dumps(df.index))
# e = time.time()  # 0.004, 快10-20%

# print(e-s)


# s = time.time()


# _columns = ['amount', 'bfq_close', 'bfq_high', 'bfq_low', 'bfq_open', 'close',
#             'high', 'liquidity', 'low', 'open', 'shares', 'volume']
# serieses = list()

# for c in _columns:
#     v = pickle.loads(
#         db.get(force_bytes(c)))
#     serieses.append(v)

# df = pd.concat(serieses, axis=1)
# df = handler_result(df)


# e = time.time()  # 0.004, 快10-20%

# print(e-s)
