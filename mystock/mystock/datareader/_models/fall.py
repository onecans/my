'''
用于计算跌幅
'''
from collections import defaultdict

from django.db import models


class PriceFallSetup(models.Model):
    name = models.CharField(max_length=50)
    start = models.DateField(blank=True, null=True, verbose_name='起始日期')
    end = models.DateField(blank=True, null=True, verbose_name='结束日期')
    ranges = models.TextField(blank=True, null=True, default='-99999,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,99999')

    class Meta:
        verbose_name = '跌幅统计设定'

    def __str__(self):
        return self.name

    def get_url(self):
        return '/code_info/start/end/{code}?col=low,high'

    def fetch(self, data=None, market_size=None):
        dfs = {}
        if data:
            dfs = data

        else:
            fetch = AioHttpFetch()
            rsts = fetch.x_fetch(self.get_url(), test=self.test, where=self.where)
            for rst in rsts:
                dfs[rst['paras']['line'].split(':')[0]] = pd.DataFrame.from_dict(rst['result'])

            market_size = fetch.x_get_marketsize(where=self.where)

            market_size = pd.DataFrame.from_dict(market_size)
            market_size.index = pd.DatetimeIndex(market_size.index)

        dd = defaultdict(list)
        chg_range = [float(i) for i in self.ranges.split(',')]
        for code, df in dfs.items():

            df = df[(df.index >= self.start.strftime('%Y-%m-%d')) & (df.index <= self.end.strftime('%Y-%m-%d'))]

            if df.empty:
                continue
            high_idx = df.high.idxmax()

            df_low = df[(df.index >= high_idx)]

            # change = (max(df.high) / min(df_low.low)) if min(df_low.low) != 0 else 9999
            change = (max(df.high) - min(df_low.low)) / max(df.high) if max(df.high) != 0 else 9999

            i = 0
            j = 1
            while True:
                if chg_range[i] < change <= chg_range[j]:
                    dd[(chg_range[i], chg_range[j])].append(code)
                    break
                i += 1
                j += 1

        end_market_size = market_size.loc[self.end]['cnt']
        start_market_size = market_size.loc[self.start]['cnt']

        objs = []
        for chg_range, codes in dd.items():
            detail = PriceFallDetail(setup=self, fall_range_start=chg_range[0], fall_range_end=chg_range[1],
                                     codes=','.join(codes), end_market_size=end_market_size, start_market_size=start_market_size)
            objs.append(detail)

        PriceFallDetail.objects.filter(setup=self).delete()
        if objs:
            PriceFallDetail.objects.bulk_create(objs)


class PriceFallDetail(models.Model):
    setup = models.ForeignKey(PriceFallSetup, verbose_name='期间设定')
    fall_range_start = models.FloatField(verbose_name='区间开始')
    fall_range_end = models.FloatField(verbose_name='区间结束')
    codes = models.TextField(blank=True, null=True)

    end_market_size = models.IntegerField(blank=True, null=True, verbose_name='期末股票总数')
    start_market_size = models.IntegerField(blank=True, null=True, verbose_name='期初股票总数')

    def _profit(self):
        return round(len(self.codes.split(','))/self.end_market_size, 4)

    _profit.short_description = '比率'
    profit = property(_profit)
