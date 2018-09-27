from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import *

# Register your models here.


@admin.register(PeriodMinCnt)
class PeriodMinCntAdmin(admin.ModelAdmin):
    list_display = ('where', 'get_period',
                    # 'profit',
                    'min_cnt',
                    #  'market_size',
                    # 'get_codes',
                    # 'test',
                    'start_market_size',
                    'end_market_size',
                    'end_profit',
                    'profit_without_new',
<<<<<<< HEAD
                    'period_end', 'new_cnt','old_low_cnt'
=======
                    'period_end',
>>>>>>> 7d6ee038d69902d770c53f6ce9f88eb6d520d458

                    )

    list_filter = ('where',)
    search_fields = ('period_start',)
    actions = ['fetch', 'compare_codes']
    actions_on_top = True
    list_per_page = 1000

    def get_codes(self, obj):
        return obj.codes.split(',') if obj.codes else []

    def fetch(self, request, qs):
        for o in qs:
            o.fetch()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs
        return qs.filter(period_start__in=('1990-12-19', '2002-01-22',
                                           '2016-01-27', '2001-06-14', '2014-07-21', '2007-10-16', '1999-06-30', '1997-05-12', '1994-09-13', '1999-05-18', '2005-06-03',
                                           '1993-02-16', '2004-04-09', '2009-08-06', '2001-06-14', '2018-01-29', '1994-08-01', '1996-01-19', '2005-07-11',
                                           '2015-06-15', '1992-05-26', '1992-11-17', '2005-07-19', '2008-11-04', '2009-08-05', '1994-7-29')).order_by('period_start', 'period_end')

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

        rst = f'<table><tr><td>{t}</td>'
        for x in obj.cnts.split('~'):
            r, c = x.split(':')
            if float(r) < 0:
                continue
            rst += f'<td>{r}</td>'

        rst += '</tr><tr><td>数量</td>'
        for x in obj.cnts.split('~'):
            r, c = x.split(':')
            if float(r) < 0:
                continue
            p = round(int(c) / s, 2)
            rst += f'<td>{c}<br>{p}</td>'

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
