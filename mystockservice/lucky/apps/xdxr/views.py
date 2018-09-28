from aiohttp import web

from lucky.base.response import json_response

rounters = web.RouteTableDef()


@routes.post('/xdxr/{file_name}', name='post_xdxr_file')
async def post_xdxr_file(request):
    file_name = request.match_info['file_name']
    rst = await services.post_file(request.app, file_name)
    return json_response(rst)
