from .models import *
from django.db.models import Q
ASSERT_OVERVIEW_FIELDS = ['资产总计','负债合计','所有者权益合计','货币资金']
PROFIT_OVERVIEW_FIELDS = ['营业总收入','营业收入','营业总成本','营业成本','财务费用','营业利润(亏损以“-”号填列)']
try:
    FORMULA_NAME = [f.name for f in Formula.objects.filter(Q(manual__isnull=True) | Q(manual = ''))]

    ASSERT_OVERVIEW_FIELDS += FORMULA_NAME

    ASSERT_CAL_FIEDLS =[f.name for f in Formula.objects.filter(Q(manual__isnull=False) & ~Q(manual = ''))] 
except:
    pass