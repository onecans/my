from . import base_info, code_info, db


class IndexDb(db.DatetimeIndexMixin, db.DfDb):
    prefix = 'index_'

    def __init__(self, index_code, **kwargs):
        super().__init__(**kwargs)
        self.db = self.db.prefixed_db(db.force_bytes(self.prefix+index_code))


def caculate(index_code, codes, start_date, column='close' initial=1000):
    if not index_code.startswith('800'):
        raise ValueError('index_code 必须以800开头')
    dfs = []
    for code in codes:
        df = code_info(code, columns=[column])
