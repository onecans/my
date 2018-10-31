from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, FormView, View, DetailView
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
# from django.http.response import 
from .forms import *
from .models import *
# from django.views.generic.detail import SingleObjectMixin
# Create your views here.
import pandas as pd
import datetime
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from . import report

def read_df(df, stock, report):
    df = df.stack()
    df = df.apply(lambda x: str(x).strip())
    df = df.replace('--', '0')
    min_period = '2007-12-31'
    year = datetime.datetime.now().year
    level1 = 0
    seq = 10
    value_list = []
    Value.objects.filter(stock=stock, item__report=report).delete()
    try:
        while True:
            _df = df.xs(level1)
            for idx in _df.index:
                if idx.strip() == '报告日期':
                    item_name = _df[idx].strip()
                    try:
                        item_obj = Item.objects.get(name=item_name, report=report)
                    except Item.DoesNotExist:
                        item_obj = Item(name=item_name, report=report)
                        item_obj.save()
                    continue
                period = idx
                if period.startswith('Unnamed'):
                    continue

                if period <= min_period:
                    continue

                if period <= str(year) and period.split('-')[1] != '12':
                    continue

                value = _df[idx]

                if not value or float(value) == 0:
                    continue

                obj = Value(seq=seq, item=item_obj, period=period, value=float(value), stock=stock)
                seq += 10
                value_list.append(obj)
            level1 += 1

    except KeyError:
        pass

    Value.objects.bulk_create(value_list)


def report_handler_view(request, code):
    obj = get_object_or_404(Stock, code=code)
    if request.method == 'GET':
        form = ReportHandlerForm()
        return render(request, template_name='stock/report_handler.html', context={'form': form, 'object': obj})

    if request.method == 'POST':
        form = ReportHandlerForm(request.POST)
        if form.is_valid:
            zcfzb = pd.read_csv(request.POST.get('zcfzb'), encoding='gbk')
            read_df(zcfzb, stock=obj, report='zcfzb')

            xjllb = pd.read_csv(request.POST.get('xjllb'), encoding='gbk')
            read_df(xjllb, stock=obj, report='xjllb')
            lrb = pd.read_csv(request.POST.get('lrb'), encoding='gbk')
            read_df(lrb, stock=obj, report='lrb')
            obj.calculate()
            return render(request, template_name='stock/report_handler.html', context={'form': form, 'object': obj})
        else:
            return render(request, template_name='stock/report_handler.html', context={'form': form, 'object': obj})


class ReportHandlerView(SingleObjectMixin, TemplateView):


    template_name = 'stock/report_handler.html'
    # form_class = ReportHandlerForm
    # success_url = '/stock/report_handler'
    model = Stock
    pk_url_kwarg = 'code'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = {'object': self.object}
        # print(self.object)
        return super(ReportHandlerView, self).get(request, *args, **kwargs)

    # def get_success_url(self):
    #     obj = self.get_object()
    #     # print('get_success_url', obj)
    #     return '/stock/report_handler/{pk}'.format(pk=obj.code)
    # # def get_context_data(self, **kwargs):
    #     context = super(ReportHandlerView, self).get_context_data(**kwargs)
    #     print('context',context)
    #     print(self.request.GET.get('code'))
    #     return context
    #     print('get_context_data',kwargs)

    #
    #
    #     super(ReportHandlerView, self).get_context_data(**kwargs)

    # def get(self, request, **kwargs):
    #     print(kwargs)
    #     stock_id = kwargs.get('pk')
    #     stock = get_object_or_404(Stock, pk=stock_id)
    #     form = ReportHandlerView.form_class(data={'stock':stock})
    #     kwargs['form'] = form
    #     return super(ReportHandlerView, self).get(request, kwargs)

    def post(self, reqeust, code):
        print(self.request.POST)
        if 'import' in self.request.POST:
            obj = self.get_object()

        # print('form_vaid', form)
        # return super().form_valid(form)

class DfsView(TemplateView):
    template_name = 'stock/dfs.html'

    def show_df(self, dfs):
    
        rst = []

        pd.options.display.float_format = '{:,}'. format
    
        for df in dfs:
            if hasattr(df,  '_NAME'):
                rst.append({'title': df._NAME, 'html': df.to_html()})
            else:
                rst.append({'title': '-----------', 'html': df.to_html()}) 

        return render(self.request, template_name=DfsView.template_name, context={'dfs': rst})



class GroupReportView(FormView):

    form_class = GroupReportForm
    template_name = 'stock/group_report.html'

    def form_valid(self, form):

        dfs = report._get_assert_dfs(period=form.cleaned_data['period'], stocks=form.cleaned_data['group'].stocks.all())
        # return render()
        view = DfsView(request=self.request)
        return view.show_df(dfs)
