from django.shortcuts import render
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from .forms import *
from .models import *
from . import config as rpt_config 
# Create your views here.
import re
import pandas as pd
from django.db.models import Q
from imp import reload
from django_pandas.io import read_frame


def show_df(request, dfs):
    # def float_format(x):
    #     return '{:,.0}'. format(x / 1000)
    rst = []

    pd.options.display.float_format = '{:,}'. format
    
    for df in dfs:
        if hasattr(df,  '_NAME'):
            rst.append({'title': df._NAME, 'html': df.to_html()})
        else:
            rst.append({'title': '-----------', 'html': df.to_html()}) 

    return render(request, template_name='report/dfs.html', context={'dfs': rst})


def group_report_view(request):

    def _get_assert_dfs(report_type, year, codes):
        df = read_frame(Value.objects.filter(report__report_type=report_type, report__year=year, report__stock__code__in=codes, report__name='资产负债表'), fieldnames=[
                        'report', 'seq', 'item', 'report__stock__code', 'report__year', 'report__quarter', 'report__report_type', 'report__unit','value', ])
        df.value = df['value'] * df['report__unit']
        df1 = df.copy()
        df1.drop(['seq','report__year','report__quarter','report__report_type','report__unit'], inplace=True, axis=1)
        df1 = df1[df1['item'].isin( rpt_config.ASSERT_OVERVIEW_FIELDS)]
        df1 = pd.pivot_table(df1, index=['report','report__stock__code'], columns=['item'])
        df1['value'] = df1['value'].apply( lambda x : round(x/1000,0) ) 
        df1._NAME = '资产负债损益总览(单位:千元)'
        print(df1)

        df2 = df.copy()
        df2.drop(['seq','report__year','report__quarter','report__report_type'], inplace=True, axis=1)
        df2 = df2[df2['item'].isin(rpt_config.ASSERT_CAL_FIEDLS)]
        df2 = pd.pivot_table(df2, index=['report','report__stock__code','report__unit'], columns=['item'])  
        df2['value'] = df2['value'].apply( lambda x : (round(x*100,2))  ) 
        df2._NAME = '资产负债表计算项'

        return df, [df1, df2]

    def _get_profit_dfs(report_type, year, codes):
        df = read_frame(Value.objects.filter(report__report_type=report_type, report__year=year, report__stock__code__in=codes, report__name='利润表'), fieldnames=[
                        'report', 'seq', 'item', 'report__stock__code', 'report__year', 'report__quarter', 'report__report_type', 'report__unit','value', ])
        df.value = df['value'] * df['report__unit']
        df1 = df.copy()
        df1.drop(['seq','report__year','report__quarter','report__report_type','report__unit'], inplace=True, axis=1)
        df1 = df1[df1['item'].isin( rpt_config.PROFIT_OVERVIEW_FIELDS)]
        df1 = pd.pivot_table(df1, index=['report','report__stock__code'], columns=['item'])
        df1['value'] = df1['value'].apply( lambda x : round(x/1000,0) ) 
        df1._NAME = '利润表总览(单位:千元)'
        print(df1)

        df2 = df.copy()
        df2.drop(['seq','report__year','report__quarter','report__report_type'], inplace=True, axis=1)
        df2 = df2[df2['item'].isin(rpt_config.ASSERT_CAL_FIEDLS)]
        df2 = pd.pivot_table(df2, index=['report','report__stock__code','report__unit'], columns=['item'])  
        df2['value'] = df2['value'].apply( lambda x : (round(x*100,2))  ) 
        df2._NAME = '资产负债表计算项'

        return df, [df1, df2]


    reload(rpt_config)
    if request.method == 'GET':
        form = GroupReportForm()
        return render(request, template_name='report/group_report.html', context={'form': form})
    if request.method == 'POST':
        form = GroupReportForm(request.POST)
        if not form.is_valid():
            return render(request, template_name='report/group_report.html', context={'form': form})

        group = form.cleaned_data['group']
        year = form.cleaned_data['year']
        report_type = form.cleaned_data['report_type']
        codes = [stock.code for stock in group.stocks.all()]
        
        assert_df, assert_show_dfs = _get_assert_dfs(report_type, year, codes)
        
        profit_df, profit_show_dfs = _get_profit_dfs(report_type, year, codes)  


        tmp = assert_show_dfs
        tmp.extend(profit_show_dfs)
        tmp.append(assert_df)
        tmp.append(profit_df)
        print(tmp)
        return show_df(request, tmp)


class ReportImportView(FormView):
    template_name = 'report/report_import.html'
    form_class = ReportImportForm
    success_url = '/report_import/'

    def form_valid(self, form):
        if 'import' in form.data:

            report = form.cleaned_data['report']
            lines = form.cleaned_data['data'].splitlines(keepends=False)
            amount_re = form.cleaned_data['amount_re']
            item_re = form.cleaned_data['item_re']
            item_index = 0
            amount_index = '0,0'  # 期末
            # amount_index = '1,0' # 期初

            error_item = Item.objects.get(name='ERROR_ITEM')

            Value.objects.filter(report=report).delete()

            for seq, line in enumerate(lines):
                try:
                    item = re.findall(item_re, line)
                    amount = re.findall(amount_re, line)
                    try:
                        item_obj = Item.objects.get(name=item[item_index])
                    except:
                        item_obj = Item(name=item[item_index])
                        item_obj.save()

                    for index in amount_index.split(','):
                        amount = amount[int(index)]

                    if amount.startswith('~'):
                        amount = amount[1:]

                    amount = float(amount.replace(',', ''))

                    value = Value(seq=seq * 10, report=report, item=item_obj, value=amount, source=line)
                    # print(item_obj, amount)

                except:
                    value = Value(seq=-1 * seq * 10, report=report, item=error_item, value=0, source=line)

                value.save()
        return super(ReportImportView, self).form_valid(form)


def formula_report(request):
    if request.method == 'GET':
        form = FormulaReportForm()
        return render(request, template_name='report/formula_report.html', context={'form':form})

    if request.method == 'POST':
        form = FormulaReportForm(request.POST)
        if not form.is_valid():
            return render(request, template_name='report/formula_report.html', context={'form':form})
        else:
            report = form.cleaned_data['report']
            if report:
                formulas = Formula.objects.filter(Q(report=report) | Q(report__isnull=True))
            else:
                formulas = Formula.objects.all()
            
            adds = formulas.prefetch_related('adds')
            minus = formulas.prefetch_related('minus')
            
            adds_df = read_frame(adds, fieldnames=['id','seq','name','adds__name','stock','report'])
            adds_df['sign'] = '+'
            adds_df['item'] = adds_df['adds__name']
            minus_df = read_frame(minus,fieldnames=['id','seq','name','minus__name','stock','report'])
            minus_df['sign'] = '-'
            minus_df['item'] = minus_df['minus__name']
            if len(minus_df) == 1:
                df = adds_df
            else:
                df = pd.concat([adds_df, minus_df])

            df['report'] = report
            df['report_pk'] = report.pk if report else None
            def _fetch_value(row):
                if row['report']:
                    try:
                        value = Value.objects.get(report__pk=row['report_pk'], item__name=row['item'])
                        return value.value
                    except:
                        
                        return 'NOT FOUND'
                else:
                    return 'Nan'
            df['value']=df.apply(_fetch_value, axis=1)
            df=df[['seq','name','sign','item','report','stock','value']]
            df = df.sort_values(['seq','name','sign'])
            return show_df(request, [df])


