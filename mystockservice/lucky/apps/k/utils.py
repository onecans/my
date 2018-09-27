from collections import namedtuple

Parameters = namedtuple(
    'Parameters', 'start end code col where app query match_info')
WHERE_SH = 'SH'
WHERE_SZ = 'SZ'
WHERE_ALL = 'ALL'
WHERE_INDEX = 'INDEX'
WHERE_OTHER = 'OTHER'


def parse_file_name(file_name):
    if file_name.startswith('SH#'):
        return 'SH', file_name[3:-4]
    elif file_name.startswith('SZ#'):
        return 'SZ', file_name[3:-4]
    elif file_name[0] in ('0', '3'):
        return 'INDEX', index_key(file_name[:-4])
    else:
        return 'OTHER', file_name[:-4]


def index_key(code):
    return 'INDEX_' + code


def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]


def build_parameters(paras=None, app=None, start=None, end=None, code=None, col=None, where=None):
    if paras:
        app = app if app else paras.app
        start = start if start else paras.start
        end = end if end else paras.end
        code = code if code else paras.code
        col = col if col else paras.col
        where = where if where else paras.where
        return Parameters(app=app, start=start, end=end, code=code, col=col, where=where, query=paras.query, match_info=paras.match_info)
    else:
        return Parameters(app=app, start=start, end=end, code=code, col=col, where=where, query={}, match_info={})


def fetch_parameters(request, d_code='ALL', d_where='ALL', d_col='high', d_start=None, d_end=None):

    start = request.match_info['start'] if 'start' in request.match_info else d_start
    end = request.match_info['end'] if 'end' in request.match_info else d_end

    try:
        code = request.match_info['code']
        print('code1', code)
    except KeyError:

        code = request.query.get('code')
        code = code if code else d_code
    try:
        where = request.match_info['where']
    except KeyError:

        where = request.query.get('where')
        where = where if where else d_where
    try:
        col = request.match_info['col']
    except KeyError:

        col = request.query.get('col')
        col = col if col else d_col
    return Parameters(start=start, end=end, code=code, col=col, where=where, app=request.app, query=request.query,
                      match_info=request.match_info
                      )


def parameter_to_dict(paras):
    return dict(start=paras.start, end=paras.end,
                code=paras.code, where=paras.where)
