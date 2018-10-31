# from pytdx.util.best_ip import select_best_ip

# from pytdx.hq import TdxHq_API

# api = TdxHq_API()

# api.connect(ip=select_best_ip())


# print(api.to_df(api.get_xdxr_info(1, '600381')))


import  QUANTAXIS  as QA 

df = QA.QAFetch.QATdx.QA_fetch_get_stock_xdxr('000001')

print(df)