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


def _def_paras(request):
    if 'nocache' in request.query:
        nocache = True
    else:
        nocache = False
    return (request.match_info.get('code', None),
            request.match_info.get(
                'start', None), request.match_info.get('end', None),
            request.query.get('col', 'high'),
            nocache
            )


def _build_line(request):
    code, start, end, col, nocache = _def_paras(request)
    line = Line(code=code, app=request.app, start=start,
                end=end, col=col, nocache=nocache)
    return line


@cache(expires=60*60*12)
@routes.get('/baseinfo/{code}')
async def code_base_info(request):
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
@routes.get('/baseinfo')
async def base_info(request):
    paras = fetch_parameters(request, d_col='')
    rst = await services.loads_base_info(paras)
    return json_response(rst, paras=paras)


@cache(expires=60*60*12)
@routes.get('/code_info/{start}/{end}/{code}')
async def code_info(request):
    line = _build_line(request)
    line_df = await line.to_df()
    rst = line_df.to_dict()
    return json_response(rst, paras={'line': str(line)})


@cache(expires=60*60*12)
@routes.get('/se/codelist/{where}')
async def codelist(request):
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
@routes.get('/se/info')
async def seinfo(request):
    col = request.query.get('col')
    if not col:
        raise web.HTTPBadRequest(reason='col 必输')

    category = request.query.get('category', '')

    rst = await services.se_info(request.app, col, category)

    return json_response(rst, paras={'col': col, 'category': category})


@routes.get('/se/size')
async def se_size(request):
    paras = fetch_parameters(request)
    rst = await services.k_marketsize(paras)
    return json_response(rst, paras=paras)


@routes.get('/k/range/{start}/{end}/{code}')
async def k_range(request):
    line = _build_line(request)
    line = line.col(col='high,low')
    line_df = await line.to_df()

    rst = line_df.range(start1=line.start, end1=request.query.get(
        'start_period_end', line.start), start2=request.query.get('end_period_start', line.end), end2=line.end)
    return json_response(rst, paras={'line': str(line)})


@cache(expires=60*60*12)
@routes.get('/k/min_counter/{code}')
async def k_min_count(request):
    line = _build_line(request)
    line = line.col(col='low')
    line_df = await line.to_df()

    rst = line_df.min_count(window_size=int(request.query.get('window_size', 52*7)), resample=request.query.get('resample', '')
                            )
    return json_response(rst, paras={'line': str(line)})


@cache(expires=60*60*12)
@routes.get('/k/max_counter/{code}')
async def k_max_count(request):
    line = _build_line(request)
    line = line.col(col='high')
    line_df = await line.to_df()

    rst = line_df.max_count(window_size=int(request.query.get('window_size', 52*7)), resample=request.query.get('resample', '')
                            )
    return json_response(rst, paras={'line': str(line)})


# @cache(expires=60*60*12)
# @routes.get('/k/min_max_counter2/{code}')
# async def k_min_max_counter2(request):
#     paras = fetch_parameters(request, d_start='start', d_end='end')
#     rst = await services.k_min_max_counter(paras)
#     return json_response(rst, paras=paras)


@cache(expires=60*60*12)
@routes.get('/k/min_k/{start}/{end}/{code}')
async def min_k(request):
    line = _build_line(request)
    col = request.query.get('col', '')
    if not col:
        raise web.HTTPBadRequest()
    line = line.col(col=col)
    line_df = await line.to_df()
    k = request.query.get('k', '10')
    line_df = line_df.min_k(k=int(k))
    return json_response(line_df.to_dict(), paras={'line': str(line)})


# @cache(expires=60*60*12)
# @routes.get('/k/line/{start}/{end}/{code}')
# async def line(request):
#     parameters = fetch_parameters(request, d_col='high')
#     rst = await services.line(parameters)

#     return json_response(rst, paras=parameters)


# @cache(expires=60*60*12)
# @routes.get('/k/combin/{start}/{end}/{code}')
# async def combin(request):

#     rst = {}
#     if 'line' in request.query:
#         parameters = fetch_parameters(request, d_col='high')
#         rst['line'] = await services.line(parameters)

#     if 'volume' in request.query:
#         parameters = fetch_parameters(request, d_col='volume')
#         rst['volume'] = await services.volume(parameters)

#     if 'describe' in request.query:
#         paras = fetch_parameters(request)
#         tmp = await services.describe(paras)
#         rst['describe'] = tmp[0]

#     if 'baseinfo' in request.query:
#         paras = fetch_parameters(request, d_col='name,totals')
#         rst['baseinfo'] = await services.loads_base_info(paras)

#     return json_response(rst, paras=fetch_parameters(request))


# @cache(expires=60*60*12)
# @routes.get('/k/min/{start}/{end}/{code}')
# async def k_min(request):
#     paras = fetch_parameters(request)
#     rst = await services.k_min(paras)
#     return json_response(rst, paras=paras)


# @cache(expires=60*60*12)
# @routes.get('/k/max/{start}/{end}/{code}')
# async def k_max(request):
#     paras = fetch_parameters(request)
#     rst = await services.k_max(paras)
#     return json_response(rst, paras=paras)
