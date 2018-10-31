
import datetime
import json

from aiohttp import web

from .parameter import Parameters, parameter_to_dict


def json_response(data=web.helpers.sentinel, *, paras=None, text=None, body=None, status=200,
                  reason=None, headers=None, content_type='application/json',
                  dumps=json.dumps):
    if data is not web.helpers.sentinel:
        if text or body:
            raise ValueError(
                "only one of data, text, or body should be specified"
            )
        else:
            rst = {}
            if paras is not None:
                if isinstance(paras, Parameters):
                    rst['paras'] = parameter_to_dict(paras)
                else:
                    rst['paras'] = paras

            rst['datetime'] = datetime.datetime.isoformat(
                datetime.datetime.now())
            rst['result'] = data
            text = dumps(rst)
    return web.Response(text=text.replace(' NaN', ' null'), body=body, status=status, reason=reason,
                        headers=headers, content_type=content_type)
