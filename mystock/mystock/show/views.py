import math

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from pyecharts import Page

from . import charts


def line_with_min_volume(request, start, end, code):
    print(code)

    if code.upper() != 'ALL':
        codes = [code, ]
    else:
        codes = settings.CODES_SEENING
    chart = charts.line_with_min_volume(start, end, codes)

    return show(request, chart)


def show(request, chart):

    template = loader.get_template('show/pyecharts.html')
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
