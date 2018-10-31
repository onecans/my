import pandas as pd
df = pd.read_csv('mystock/datareader/data/sse/sh_final.csv')

df.index = pd.DatetimeIndex(df.date)
del df['Unnamed: 0']
del df['date']
df = df.sort_index()
df.to_csv('mystock/datareader/data/sse/sh_sse_day_overview.csv', index_label='date')

# # df = pd.read_csv('mystock/datareader/data/sse/sh_sse_day_overview.csv')
# # print(df['Unnamed: 0'])
# # df.index = pd.DatetimeIndex( df['Unnamed: 0'])
# # print(df)
# # print(df.columns)

# df.to_csv
