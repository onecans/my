
# Create your views here.
from __future__ import unicode_literals

import math

import requests
from datareader import echart
from datareader.echart import *
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.views.generic import FormView
from pyecharts import Line, Overlap, Page

from . import services
from .forms import *


def index(request, method, code):
    index = request.GET.get('index', False)
    if index:
        index = True

    if method == 'rzrq':
        chart = rzrq(code, index=index)
    elif method == 'get_line':
        chart = get_line(code, index=index)[0]
    else:
        run = getattr(echart, method)
        chart = run(code)
    return show(request, chart)


def range(request, start, end):
    where = request.GET.get('where', 'SH')
    fq_type = request.GET.get('fq_type', 'qfq')
    chart, _, _ = get_range_bar(start, end,  where=where, fq_type=fq_type)

    return show(request, chart)


def grow_range(request, start, end):
    where = request.GET.get('where', 'SH')
    fq_type = request.GET.get('fq_type', 'qfq')
    chart, _, _ = get_grow_range_bar(start, end,  where=where, fq_type=fq_type)

    return show(request, chart)


def max_date(request, start, end):
    where = request.GET.get('where', 'SH')
    fq_type = request.GET.get('fq_type', 'qfq')
    val_name = request.GET.get('val_name', 'high.idxmax')

    chart, _, _ = get_max_date_bar(start, end, where=where, fq_type=fq_type, val_name=val_name)

    return show(request, chart)


def show(request, chart):

    template = loader.get_template('datareader/pyecharts.html')
    if isinstance(chart, Page):
        for _chart in chart:
            _chart.height = 600
            _chart.width = 1200
            _chart._option['dataZoom'] = [{'show': True, 'type': 'slider', 'start': 0,
                                           'end': 100, 'orient': 'horizontal', 'xAxisIndex': None, 'yAxisIndex': None}]
            _chart._option['tooltip']['axisPointer'] = {'animation': False,
                                                        'type': "cross",
                                                        'crossStyle': {
                                                            'color': "#376DF4"
                                                        }}
    else:
        chart.height = 600
        chart.width = 1200
        chart._option['dataZoom'] = [{'show': True, 'type': 'slider', 'start': 0,
                                      'end': 100, 'orient': 'horizontal', 'xAxisIndex': None, 'yAxisIndex': None}]
        chart._option['tooltip']['axisPointer'] = {'animation': False,
                                                   'type': "cross",
                                                   'crossStyle': {
                                                       'color': "#376DF4"
                                                   }}

    context = dict(
        myechart=chart.render_embed(),
        host=settings.PYECHART_REMOTE_HOST,
        script_list=chart.get_js_dependencies()
    )
    return HttpResponse(template.render(context, request))


class KSearchView(FormView):
    form_class = KSearchForm
    template_name = 'datareader/k_search.html'

    def form_valid(self, form):

        line1 = Line()
        val1 = services.line(form.cleaned_data['code1'], form.cleaned_data['start'], form.cleaned_data['end'],
                             form.cleaned_data['col1'], form.cleaned_data['is_index1'])

        line1.add(services.code_str(form.cleaned_data['code1']), list(val1.keys()), list(val1.values()))

        line2 = Line()
        val2 = services.line(form.cleaned_data['code2'], form.cleaned_data['start'], form.cleaned_data['end'],
                             form.cleaned_data['col2'], form.cleaned_data['is_index2'])
        line2.add(services.code_str(form.cleaned_data['code2']), list(val2.keys()), list(val2.values()))

        overlap = Overlap('%s-%s' % (form.cleaned_data['start'], form.cleaned_data['end']))
        overlap.add(line1)
        overlap.add(line2, yaxis_index=1, is_add_yaxis=True)

        return show(self.request, overlap)
