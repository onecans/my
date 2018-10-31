from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import *

# Register your models here.


@admin.register(PeriodMinCnt)
class PeriodMinCntAdmin(admin.ModelAdmin):
    list_display = ('where', 'period_start', 'period_end',
                    # 'profit',
                    'min_cnt',
                    #  'market_size',
                    # 'get_codes',
                    # 'test',
                    'start_market_size',
                    'end_market_size',
                    'end_profit',
                    'profit_without_new',
                    'new_cnt', 'old_low_cnt',
                    'profit_shares',
                    'profit_liquidity',
                    'final'

                    )
    list_editable = ('final',
                     #  'period_end'
                     )
    list_filter = ('where', 'final')
    search_fields = ('period_start',)
    actions = ['fetch', 'compare_codes', 'copy']
    actions_on_top = True
    list_per_page = 100

    def get_codes(self, obj):
        return obj.codes.split(',') if obj.codes else []

    def fetch(self, request, qs):
        for o in qs:
            o.fetch()

    def copy(self, request, qs):
        for obj in qs:
            PeriodMinCnt(where=obj.where, period_start=obj.period_start, period_end=obj.period_end).save()

    def get_period(self, obj):
        s, e = obj.period
        if s == e:
            return s
        else:
            return obj.period

    get_period.short_description = '期间'

    def compare_codes(self, request, qs):
        if len(qs) != 2:
            messages.error(request, '必须选择两个值')
            return

        o, t = qs[0], qs[1]

        if o.where != t.where:
            messages.error(request, 'where 必须相等')
        o_codes = o.codes.split(',')
        t_codes = t.codes.split(',')
        tmp = [c for c in o_codes if c not in t_codes]
        messages.info(request, '%s 破新低数量：%s, 其中未在%s破新低数量: %s, 占比: %s, codes: %s' % (self.get_period(o), o.min_cnt,
                                                                                    self.get_period(t), len(tmp), round(len(tmp)/o.min_cnt, 2), tmp))

        tmp = [c for c in t_codes if c not in o_codes]
        messages.info(request, '%s 破新低数量: %s, 其中未在%s破新低数量: %s, 占比: %s, codes: %s' % (self.get_period(
            t), t.min_cnt, self.get_period(o),  len(tmp), round(len(tmp)/o.min_cnt, 2), tmp))

        tmp = [c for c in t_codes if c in o_codes]
        messages.info(request, '同时破新低的股票数量：%s, codes: %s' % (len(tmp), tmp))

    # def show(self, request, qs):


@admin.register(RangeAnalyse)
class RangeAnalyseAdmin(admin.ModelAdmin):
    list_display = ('where', 'start_period_start', 'start_period_end',
                    'end_period_start', 'end_period_end', 'get_cnts', 'test', 'decline')
    list_filter = ()
    search_fields = ()

    actions = ['fetch']

    def get_codes(self, obj):
        return obj.codes.split(',') if obj.codes else []

    def fetch(self, request, qs):
        for o in qs:
            o.fetch()

    def get_cnts(self, obj):
        if not obj.cnts:
            return None
        if obj.decline:
            t = '跌幅'
        else:
            t = '涨幅'
        s = 0
        for x in obj.cnts.split('~'):
            r, c = x.split(':')
            s += int(c)

        rst = '<table><tr><td>{t}</td>'.format(**locals())
        for x in obj.cnts.split('~'):
            r, c = x.split(':')
            if float(r) < 0:
                continue
            rst += '<td>{r}</td>'.format(**locals())

        rst += '</tr><tr><td>数量</td>'
        for x in obj.cnts.split('~'):
            r, c = x.split(':')
            if float(r) < 0:
                continue
            p = round(int(c) / s, 2)
            rst += '<td>{c}<br>{p}</td>'.format(**locals())

        rst += '</tr></table>'

        return format_html(rst)


@admin.register(RangeAnalyseHelper)
class RangeAnalyseHelperAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_filter = ()
    search_fields = ()


class MarketDateAnalyseAdminForm(forms.ModelForm):

    date_group = forms.fields.CharField()

    class Meta:
        model = models = MarketDateAnalyse
        fields = "__all__"


@admin.register(MarketDateAnalyse)
class MarketDateAnalyseAdmin(admin.ModelAdmin):
    form = MarketDateAnalyseAdminForm
    list_display = ('date', 'date_type', 'cnt',
                    'get_pre_sum', 'get_profit', 'get_sum'
                    # 'codes'
                    )
    list_filter = ('date_type',)
    search_fields = ()

    list_per_page = 1000

    actions = ['fetch_by_month', 'fetch_by_year']

    def fetch_by_month(self, request, qs):
        MarketDateAnalyse.objects.fetch()

    def fetch_by_year(self, request, qs):
        MarketDateAnalyse.objects.fetch('Y')

    def get_pre_sum(self, obj):
        if not obj.pre_sum_cnt:
            obj.pre_sum_cnt = MarketDateAnalyse.objects.filter(
                date__lt=obj.date).aggregate(models.Sum('cnt'))['cnt__sum']
            obj.save()
        return obj.pre_sum_cnt

    def get_sum(self, obj):
        if not obj.sum_cnt:
            if self.get_pre_sum(obj):
                obj.sum_cnt = self.get_pre_sum(obj) + obj.cnt
            else:
                obj.sum_cnt = obj.cnt
                obj.save()
        return obj.sum_cnt

    def get_profit(self, obj):
        x = self.get_sum(obj)
        if x:
            return round(obj.cnt/x, 2)


@admin.register(MarketInfo)
class MarketInfoAdmin(admin.ModelAdmin):
    list_display = ('date', 'is_min',
                    # 'is_max', 'up_profit',
                    'market_size', 'min_liquidity_profit', 'min_shares_profit',
                    # 'max_liquidity_profit', 'max_shares_profit',
                    # 'avg_close'
                    )
    list_filter = ()
    search_fields = ()

    actions = ['refresh']

    list_per_page = 1000

    def refresh(self, request, qs):
        MarketInfo.objects.refresh()


@admin.register(PeriodMinCnt2)
class PeriodMinCnt2Admin(admin.ModelAdmin):
    list_display = ('period_start', 'period', 'period_end',
                    # 'profit',
                    'min_cnt',
                    #  'market_size',
                    # 'get_codes',
                    # 'test',
                    'start_market_size',
                    'end_market_size',
                    'end_profit',
                    'profit_without_new',
                    'new_cnt', 'old_low_cnt',
                    'profit_shares',
                    'profit_liquidity',
                    'profit_shares2',
                    'profit_liquidity2',
                    'final',
                    'point_flag'

                    )
    list_editable = ('final', 'point_flag')
    list_filter = ('where', 'final', 'point_flag')
    search_fields = ('period_start',)
    actions = ['fetch', 'compare_codes', 'copy']
    actions_on_top = True
    list_per_page = 1000

    def get_codes(self, obj):
        return obj.codes.split(',') if obj.codes else []

    def get_url(self):
        return '/code_info/start/end/{code}?col=low,shares,liquidity,bfq_low'

    def fetch(self, request, qs):
        fetch = AioHttpFetch()
        rsts = fetch.x_fetch(self.get_url(), test=False, where='ALL')
        market_size = fetch.x_get_marketsize(where='ALL')
        dfs = {}
        for rst in rsts:
            dfs[rst['paras']['line'].split(':')[0]] = pd.DataFrame.from_dict(rst['result'])

        for o in qs:
            print(o.period_start, o.period_end)
            o.fetch(dfs, market_size)

    def copy(self, request, qs):
        for obj in qs:
            PeriodMinCnt2(where=obj.where, period_start=obj.period_start, period_end=obj.period_end).save()

    def get_period(self, obj):
        s, e = obj.period
        if s == e:
            return s
        else:
            return obj.period

    get_period.short_description = '期间'

    def compare_codes(self, request, qs):
        if len(qs) != 2:
            messages.error(request, '必须选择两个值')
            return

        o, t = qs[0], qs[1]

        if o.where != t.where:
            messages.error(request, 'where 必须相等')
        o_codes = o.codes.split(',')
        t_codes = t.codes.split(',')
        tmp = [c for c in o_codes if c not in t_codes]
        messages.info(request, '%s 破新低数量：%s, 其中未在%s破新低数量: %s, 占比: %s, codes: %s' % (self.get_period(o), o.min_cnt,
                                                                                    self.get_period(t), len(tmp), round(len(tmp)/o.min_cnt, 2), tmp))

        tmp = [c for c in t_codes if c not in o_codes]
        messages.info(request, '%s 破新低数量: %s, 其中未在%s破新低数量: %s, 占比: %s, codes: %s' % (self.get_period(
            t), t.min_cnt, self.get_period(o),  len(tmp), round(len(tmp)/o.min_cnt, 2), tmp))

        tmp = [c for c in t_codes if c in o_codes]
        messages.info(request, '同时破新低的股票数量：%s, codes: %s' % (len(tmp), tmp))

    # def show(self, request, qs):


@admin.register(ChgSetup)
class ChgSetupAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_filter = ()
    search_fields = ()

    actions = ['fetch']

    def get_url(self):
        return '/code_info/start/end/{code}?col=low,high'

    def fetch(self, request, qs):
        fetch = AioHttpFetch()
        rsts = fetch.x_fetch(self.get_url(), test=False, where='ALL')
        dfs = {}
        for rst in rsts:
            dfs[rst['paras']['line'].split(':')[0]] = pd.DataFrame.from_dict(rst['result'])

        for o in qs:
            o.fetch(dfs)


@admin.register(ChgDetail)
class ChgDetailAdmin(admin.ModelAdmin):
    list_display = ('setup', 'fall', 'fall_range_start', 'fall_range_end', 'get_codes')
    list_filter = ('setup', 'fall')
    search_fields = ()

    def get_codes(self, obj):
        return obj.codes.split(',') if obj.codes else []
