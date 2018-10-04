from pyecharts import *

from .backend import Combin


def line_with_min_volume(start, end, codes, k=20):
    page = Page()
    for code in codes:
        c = Combin(start=start, end=end, code=code, volume=True, line=True, k=k, baseinfo=True)
        data = c.result()['result']
        overlap = Overlap()
        line = Line()
        name = data['baseinfo']['name'][code]
        title = '{code}:{name}~{start}~{end}'.format(**locals())
        line.add(title, [x for x in data['line'].keys()],
                 [x for x in data['line'].values()],  is_more_utils=True)
        overlap.add(line)
        s = Scatter()
        mink = data['volume']['mink']
        x = [x for x in mink.keys() if x not in ('mean')]
        y = [1] * len(x)
        s.add('最小成交', x, y)
        overlap.add(s)
        page.add(overlap)

    return page
