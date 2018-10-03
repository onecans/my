import itertools
import pickle
import sys
import zlib
from collections import Iterable, OrderedDict, defaultdict

import pandas as pd

import mystockdata
from lucky.apps.k.utils import *


def force_decode(f):
    async def warp(*args, **kwargs):
        rst = await f(*args, **kwargs)
        if hasattr(rst, 'decode'):
            return rst.decode()
        if isinstance(rst, dict):
            return {key: value.decode() for key, value in rst.items()}
        if isinstance(rst, list):
            return [x.decode() for x in rst]
        return rst
    return warp


async def code_list(where):
    return mystockdata.code_list(where=where)


async def loads_base_info(columns, codes=None):
    print(columns, codes)
    df = mystockdata.base_info(columns, codes)
    return df


async def code_info(code, columns=None):
    return mystockdata.code_info(code, columns)
