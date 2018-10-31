from .models import Value
from django_pandas.io import read_frame
from . import config as rpt_config
import pandas as pd
from imp import reload

def _get_pivot_df(period, stocks, fields):
    print('fetch data: ', fields)
    df = read_frame(Value.objects.filter( period=period, stock__in=stocks), fieldnames=[
                    'period', 'seq', 'item', 'stock' ,'value', ])
    df.drop(['seq','period'], axis=1, inplace=True)
    df = df[df['item'].isin(fields)]
    df = pd.pivot_table(df, index='stock', columns=['item'])
    print(df.head(5))
    return df

def _get_assert_dfs( period, stocks):
    reload(rpt_config)
    rst = []
    
    df1 = _get_pivot_df(period, stocks, rpt_config.OVERVIEW_FIELDS)
    
    sum_df = df1.apply(sum)
    sum_df.name = '汇总'

    df1 = df1.append(sum_df) 
    df1._NAME = '总览'

    df2 = round(df1*100/sum_df,2) 
    df2._NAME = '总览比例'

    rst = [df1, df2]

    df3 = _get_pivot_df(period, stocks, rpt_config.CACULATE_FIELDS)
    df3 = round(df3*100,2)
    rst.append(df3) 
    return rst
