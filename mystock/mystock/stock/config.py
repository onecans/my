from .models import *
from django.db.models import Q
OVERVIEW_FIELDS = ['zcfzb-资产总计(万元)','zcfzb-负债合计(万元)','zcfzb-所有者权益(或股东权益)合计(万元)',
'zcfzb-货币资金(万元)','lrb-营业总收入(万元)','lrb-营业收入(万元)','lrb-营业总成本(万元)','lrb-营业成本(万元)','lrb-财务费用(万元)','lrb-营业利润(万元)']
# PROFIT_OVERVIEW_FIELDS = ['营业总收入','营业收入','营业总成本','营业成本','财务费用','营业利润(亏损以“-”号填列)']
try:
    FORMULA_NAME = ['formula-'+f.name for f in Formula.objects.filter(Q(manual__isnull=True) | Q(manual = ''))]
    print(FORMULA_NAME)
    OVERVIEW_FIELDS += FORMULA_NAME

    CACULATE_FIELDS =['formula-'+f.name for f in Formula.objects.filter(Q(manual__isnull=False) & ~Q(manual = ''))] 
    print(CACULATE_FIELDS)
except:
    pass