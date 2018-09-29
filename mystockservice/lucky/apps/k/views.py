import asyncio
import datetime
import json
import math
import os
import time
from collections import defaultdict, namedtuple
from concurrent.futures import ProcessPoolExecutor
from json import JSONEncoder

import aioredis
import pandas as pd
from aiohttp import web

from aiohttp_cache import cache
from lucky.base.parameter import (Parameters, build_parameters,
                                  fetch_parameters, parameter_to_dict)
from lucky.base.response import json_response

from . import services
from .query import Line, LineDf
from .utils import chunk

routes = web.RouteTableDef()

# @routes.get('/k/_load/{key}', name='getk')
# async def get_k(request):
#     key = request.match_info['key']
#     x = await loads(request.app, key)
#     return web.Response(body=x, content_type='application/json')


@routes.post('/upload/{file_name}', name='postfile')
async def post_file(request):
    file_name = request.match_info['file_name']
    rst = await services.post_file(request.app, file_name)
    return json_response(rst)


@routes.get('/upload/{file_name}', name='postfile')
async def post_file2(request):
    file_name = request.match_info['file_name']
    rst = await services.post_file(request.app, file_name)
    return json_response(rst)


@routes.post('/uploadidx/{file_name}', name='postindexfile')
async def post_index_file(request):
    file_name = request.match_info['file_name']
    rst = await services.post_file(request.app, file_name, index=True)
    return json_response(rst)


@routes.post('/uploadother/{file_name}', name='postotherfile')
async def post_other_file(request):
    file_name = request.match_info['file_name']
    rst = await services.post_file(request.app, file_name, columns=None)
    return json_response(rst)

@routes.post('/baseinfo')
async def post_base_info(request):
    rst = await services.post_base_info(request.app)
    return json_response(rst)


@cache(expires=60*60*12)
@routes.get('/k/baseinfo/{code}')
async def loads_base_info(request):
    '''
    code,代码
name,名称
industry,所属行业
area,地区
pe,市盈率
outstanding,流通股本(亿)
totals,总股本(亿)
totalAssets,总资产(万)
liquidAssets,流动资产
fixedAssets,固定资产
reserved,公积金
reservedPerShare,每股公积金
esp,每股收益
bvps,每股净资
pb,市净率
timeToMarket,上市日期
undp,未分利润
perundp, 每股未分配
rev,收入同比(%)
profit,利润同比(%)
gpr,毛利率(%)
npr,净利润率(%)
holders,股东人数
    '''
    paras = fetch_parameters(request, d_col='totals')
    rst = await services.loads_base_info(paras)
    return json_response(rst, paras=paras)


@cache(expires=60*60*12)
@routes.get('/k/codes/{where}')
async def codes(request):
    where = request.match_info['where'].upper()
    if 'start_timetomarket' in request.query:
        start_timetomarket = request.query['start_timetomarket']
    else:
        start_timetomarket = None

    codes = await services.code_list(request.app, where)
    if start_timetomarket:

        codes_str = ','.join(codes)
        tmp = await services.loads_base_info(build_parameters(app=request.app, code=codes_str, col='timeToMarket'))
        tmp = tmp['timeToMarket']
        codes = [code for code, timetomarket in tmp.items()
                 if timetomarket < int(start_timetomarket)]

    return json_response(codes, paras={'where': where})


@cache(expires=60*60*12)
@routes.get('/k/describe/{start}/{end}/{code}')
async def describe(request):
    paras = fetch_parameters(request)
    rst = await services.describe(paras)
    return json_response(rst, paras=paras)


@cache(expires=60*60*12)
@routes.get('/k/describe_all/{start}/{end}')
async def describe_all(request):
    parameters = fetch_parameters(request)
    rst = await services.describe_all(parameters)
    return json_response(rst, paras=parameters)


@cache(expires=60*60*12)
@routes.get('/k/volume/{start}/{end}/{code}')
async def volume(request):
    parameters = fetch_parameters(request, d_col='volume')
    rst = await services.volume(parameters)
    return json_response(rst, paras=parameters)


@cache(expires=60*60*12)
@routes.get('/k/line/{start}/{end}/{code}')
async def line(request):
    parameters = fetch_parameters(request, d_col='high')
    rst = await services.line(parameters)

    return json_response(rst, paras=parameters)


@cache(expires=60*60*12)
@routes.get('/k/combin/{start}/{end}/{code}')
async def combin(request):

    rst = {}
    if 'line' in request.query:
        parameters = fetch_parameters(request, d_col='high')
        rst['line'] = await services.line(parameters)

    if 'volume' in request.query:
        parameters = fetch_parameters(request, d_col='volume')
        rst['volume'] = await services.volume(parameters)

    if 'describe' in request.query:
        paras = fetch_parameters(request)
        tmp = await services.describe(paras)
        rst['describe'] = tmp[0]

    if 'baseinfo' in request.query:
        paras = fetch_parameters(request, d_col='name,totals')
        rst['baseinfo'] = await services.loads_base_info(paras)

    return json_response(rst, paras=fetch_parameters(request))


@cache(expires=60*60*12)
@routes.get('/k/min/{start}/{end}/{code}')
async def k_min(request):
    paras = fetch_parameters(request)
    rst = await services.k_min(paras)
    return json_response(rst, paras=paras)


@cache(expires=60*60*12)
@routes.get('/k/max/{start}/{end}/{code}')
async def k_min(request):
    paras = fetch_parameters(request)
    rst = await services.k_max(paras)
    return json_response(rst, paras=paras)


@cache(expires=60*60*12)
@routes.get('/k/min_max_counter/{code}')
async def k_min_max_counter(request):
    paras = fetch_parameters(request, d_start='start', d_end='end')
    rst = await services.k_min_max_counter(paras)
    return json_response(rst, paras=paras)


@routes.get('/k/marketsize')
async def k_marketsize(request):
    paras = fetch_parameters(request)
    rst = await services.k_marketsize(paras)
    return json_response(rst, paras=paras)


def _def_paras(request):
    if 'nocache' in request.query:
        nocache = True
    else:
        nocache = False
    return (request.match_info.get('code', None),
            request.match_info.get(
                'start', None), request.match_info.get('end', None),
            request.query.get('col', None),
            nocache
            )


def _build_line(request):
    code, start, end, col, nocache = _def_paras(request)
    line = Line(code=code, app=request.app, start=start,
                end=end, col=col, nocache=nocache)
    return line


@routes.get('/k/line2/{start}/{end}/{code}')
async def k_line(request):
    line = _build_line(request)
    line_df = await line.to_df()
    rst = line_df.to_dict()
    return json_response(rst, paras={'line': str(line)})


@routes.get('/k/range/{start}/{end}/{code}')
async def k_range(request):
    line = _build_line(request)
    line = line.col(col='high,low')
    line_df = await line.to_df()

    rst = line_df.range(start1=line.start, end1=request.query.get(
        'start_period_end', line.start), start2=request.query.get('end_period_start', line.end), end2=line.end)
    return json_response(rst, paras={'line': str(line)})
