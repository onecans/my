
# WHERE_SH = 'SH'
# WHERE_SZ = 'SZ'
# WHERE_ALL = 'ALL'
# WHERE_INDEX = 'INDEX'
# WHERE_OTHER = 'OTHER'


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
